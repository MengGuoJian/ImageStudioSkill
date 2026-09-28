#!/usr/bin/env python3
"""ImageStudio API 生图脚本：文生图 / 图生图 / 会员状态查询。

用法（与本仓库 agnesimagegen 技能同款习惯）：
    python imagestudio_image_gen.py --prompt "一只戴围巾的橘猫" --size 1024x1024 --out out.png
    python imagestudio_image_gen.py --prompt "改成绿色" --image ref.png --out out-v2.png
    python imagestudio_image_gen.py --check

配置解析顺序：
    base_url: --base-url > 环境变量 IMAGESTUDIO_BASE_URL > ~/.imagestudio/config.json > http://127.0.0.1:8020
    api_key : --api-key  > 环境变量 IMAGESTUDIO_API_KEY  > ~/.imagestudio/config.json
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

DEFAULT_BASE_URL = "http://127.0.0.1:8020"
CONFIG_FILE = Path.home() / ".imagestudio" / "config.json"
USER_AGENT = "imagestudio-skill/1.0"


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate or edit images via the local ImageStudio service.")
    prompt = parser.add_mutually_exclusive_group()
    prompt.add_argument("--prompt")
    prompt.add_argument("--prompt-file", type=Path)
    parser.add_argument("--image", action="append", default=[], help="参考图路径/URL/data URI，可重复")
    parser.add_argument("--size", default="1024x1024", help="宽x高，例如 1024x1024")
    parser.add_argument("--n", type=int, default=1, choices=range(1, 5), help="生成数量 1-4")
    parser.add_argument("--model", default="")
    parser.add_argument("--out", type=Path, default=Path("output/imagestudio/image.png"))
    parser.add_argument("--base-url", default="")
    parser.add_argument("--api-key", help=argparse.SUPPRESS)
    parser.add_argument("--timeout", type=int, default=360)
    parser.add_argument("--retries", type=int, default=3, help="503/网络错误的重试次数")
    parser.add_argument("--check", action="store_true", help="只查询会员状态与服务可用性")
    return parser.parse_args()


def load_config() -> dict:
    if CONFIG_FILE.is_file():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8-sig"))
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def resolve_base_url(explicit: str, config: dict) -> str:
    value = (explicit or os.environ.get("IMAGESTUDIO_BASE_URL") or config.get("base_url") or DEFAULT_BASE_URL).strip()
    return value.rstrip("/")


def resolve_api_key(explicit: str, config: dict) -> str:
    value = (explicit or os.environ.get("IMAGESTUDIO_API_KEY") or config.get("api_key") or "").strip()
    return value


def image_input(value: str) -> str:
    if value.startswith(("https://", "http://", "data:image/")):
        return value
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"参考图不存在: {path}")
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


class ApiError(RuntimeError):
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


def friendly_error(status_code: int, detail: str) -> str:
    lowered = detail.lower()
    if status_code == 401:
        if "过期" in detail or "expired" in lowered:
            return "会员密钥已过期：请到 ImageStudio 会员中心激活新密钥（401）。"
        return "密钥无效或已被停用：请核对会员密钥；本机使用可不配置密钥（401）。"
    if status_code == 429:
        if "余额" in detail or "quota" in lowered:
            return "生图余额已用完：请联系管理员续费或清零（429）。"
        return "服务端号池没有可用 key：请联系管理员补充（429）。"
    if status_code == 404:
        return f"接口不存在：确认服务地址正确（404）。{detail}"
    if status_code >= 500:
        return f"上游服务错误，稍后重试（{status_code}）。{detail[:200]}"
    return f"请求失败（HTTP {status_code}）：{detail[:300]}"


def _auth_header(api_key: str) -> dict:
    """无密钥时不带 Authorization：本机部署的服务对回环请求免登录。"""
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def request_json(base_url: str, api_key: str, path: str, payload: dict | None = None, method: str = "POST",
                 timeout: int = 360, retries: int = 3) -> dict:
    url = f"{base_url}{path}"
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {**_auth_header(api_key), "User-Agent": USER_AGENT}
    if data is not None:
        headers["Content-Type"] = "application/json"
    last_error = ""
    for attempt in range(1, max(1, retries) + 1):
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            try:
                parsed = json.loads(detail)
                detail = str((parsed.get("error") or {}).get("message") or parsed.get("detail") or detail)
            except Exception:
                pass
            last_error = detail or str(exc.reason)
            if exc.code == 503 and attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise ApiError(friendly_error(exc.code, last_error), exc.code)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = str(exc)
            if "Connection refused" in last_error or "WinError 10061" in last_error:
                raise ApiError(
                    f"无法连接 ImageStudio 服务（{base_url}）：请先启动 ImageStudio.exe / start.bat。",
                    0,
                )
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise ApiError(f"网络请求失败：{last_error}")
    raise ApiError(f"请求失败：{last_error}")


def multipart_encode(fields: dict[str, str], files: list[tuple[str, str, bytes, str]]) -> tuple[bytes, str]:
    boundary = f"----imagestudio{uuid.uuid4().hex}"
    buffer = []
    for name, value in fields.items():
        buffer.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode("utf-8"))
    for field, filename, content, mime in files:
        buffer.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {mime}\r\n\r\n".encode("utf-8")
        )
        buffer.append(content)
        buffer.append(b"\r\n")
    buffer.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(buffer), boundary


def request_edit(base_url: str, api_key: str, fields: dict[str, str], image_paths: list[str], timeout: int, retries: int) -> dict:
    files = []
    for index, value in enumerate(image_paths[:4]):
        if value.startswith(("https://", "http://", "data:image/")):
            # 远程图先下载，统一以文件上传
            with urllib.request.urlopen(value, timeout=60) as response:
                content = response.read()
            filename = f"ref-{index + 1}.png"
            mime = "image/png"
        else:
            path = Path(value).expanduser().resolve()
            if not path.is_file():
                raise FileNotFoundError(f"参考图不存在: {path}")
            content = path.read_bytes()
            filename = path.name
            mime = mimetypes.guess_type(path.name)[0] or "image/png"
        files.append(("image", filename, content, mime))
    body, boundary = multipart_encode(fields, files)
    url = f"{base_url}/v1/images/edits"
    headers = {
        **_auth_header(api_key),
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "User-Agent": USER_AGENT,
    }
    last_error = ""
    for attempt in range(1, max(1, retries) + 1):
        request = urllib.request.Request(url, data=body, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            try:
                parsed = json.loads(detail)
                detail = str((parsed.get("error") or {}).get("message") or parsed.get("detail") or detail)
            except Exception:
                pass
            last_error = detail or str(exc.reason)
            if exc.code == 503 and attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise ApiError(friendly_error(exc.code, last_error), exc.code)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = str(exc)
            if "Connection refused" in last_error or "WinError 10061" in last_error:
                raise ApiError(f"无法连接 ImageStudio 服务：请先启动 ImageStudio.exe / start.bat。", 0)
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise ApiError(f"网络请求失败：{last_error}")
    raise ApiError(f"请求失败：{last_error}")


def save_result(result: dict, base_url: str, destination: Path, timeout: int) -> list[Path]:
    data = result.get("data")
    if not isinstance(data, list) or not data:
        raise ApiError(f"服务端没有返回图片：{json.dumps(result, ensure_ascii=False)[:300]}")
    saved: list[Path] = []
    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        raw: bytes | None = None
        b64 = item.get("b64_json")
        if isinstance(b64, str) and b64:
            raw = base64.b64decode(b64)
        else:
            url = item.get("url")
            if isinstance(url, str) and url:
                if url.startswith("/"):
                    url = f"{base_url}{url}"
                with urllib.request.urlopen(url, timeout=timeout) as response:
                    raw = response.read()
        if raw is None:
            continue
        if len(raw) < 1024:
            raise ApiError(f"下载的图片过小（{len(raw)} 字节），疑似异常。")
        target = destination if index == 0 else destination.with_name(
            f"{destination.stem}-{index + 1}{destination.suffix}"
        )
        target.write_bytes(raw)
        saved.append(target)
    if not saved:
        raise ApiError("服务端响应里既没有 url 也没有 b64_json。")
    return saved


def main() -> int:
    args = arguments()
    config = load_config()
    base_url = resolve_base_url(args.base_url, config)
    api_key = resolve_api_key(args.api_key or "", config)

    if args.check:
        print(f"服务地址: {base_url}")
        try:
            status = request_json(base_url, api_key, "/api/membership/status", None, method="GET",
                                  timeout=30, retries=1)
            if status.get("is_admin"):
                print("身份: 管理员（不限天数/次数）")
            else:
                days = status.get("days_remaining")
                quota = status.get("quota_remaining")
                quota_text = "不限" if status.get("quota_unlimited") else f"{quota} 次"
                days_text = "永久" if days is None else f"{days} 天"
                print(f"身份: {status.get('name') or '会员'} · 剩余 {days_text} · 生图余额 {quota_text}")
        except ApiError as exc:
            print(f"会员状态查询失败: {exc}", file=sys.stderr)
            return 1
        return 0

    if not api_key and not base_url.startswith(("http://127.0.0.1", "http://localhost", "http://[::1]")):
        print(
            f"提示：未配置会员密钥，仅支持本机 ImageStudio（免登录）。远程服务请在 {CONFIG_FILE} 配置 api_key。",
            file=sys.stderr,
        )

    prompt = ""
    if args.prompt is not None:
        prompt = args.prompt.strip()
    elif args.prompt_file is not None:
        prompt = args.prompt_file.read_text(encoding="utf-8-sig").strip()
    if not args.check and not prompt:
        raise ValueError("提示词不能为空（或使用 --check 查询会员状态）。")
    if not args.size.replace("x", "", 1).isdigit():
        raise ValueError("--size 需使用 宽x高 格式，例如 1024x1024。")

    if args.image:
        fields = {"prompt": prompt, "size": args.size, "n": str(args.n)}
        if args.model:
            fields["model"] = args.model
        result = request_edit(base_url, api_key, fields, args.image, args.timeout, args.retries)
    else:
        payload: dict = {"prompt": prompt, "size": args.size, "n": args.n, "response_format": "url"}
        if args.model:
            payload["model"] = args.model
        result = request_json(base_url, api_key, "/v1/images/generations", payload, timeout=args.timeout, retries=args.retries)

    for path in save_result(result, base_url, args.out, args.timeout):
        print(path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
