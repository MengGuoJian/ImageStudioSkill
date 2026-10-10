---
name: imagestudio
description: 通过 ImageStudio（鱼舟生图）本地服务接口生成或编辑图片；服务端使用 ChatGPT 账号池，处理会员额度与天数限制，技能不直连上游生图 API。用于游戏美术、UI 素材、插画、照片、贴图、样机、图生图编辑、多图合成，当用户提到 ImageStudio、鱼舟生图、生图、画图、图片生成、图像生成、做图、画一张图，或任何图片生成/编辑请求时使用。
---

# ImageStudio API 生图（鱼舟生图）

通过本地 **ImageStudio 服务**（默认 `http://127.0.0.1:8020`）的 `/v1/images/*` 接口生图。服务端配置 `image_api.engine=chatgpt` 时使用 ChatGPT 账号池；技能不调用 ChatGPT 或其他上游地址，也不接收上游账号凭证。`--base-url` 仅指 ImageStudio 服务地址。

> 同步说明：本技能的权威源在 FishImagen 主仓库 `skill/imagestudio`，改完后运行 `sync-skill.bat` 同步到本仓库。

## 前置条件

- **ImageStudio 服务已启动**（双击 `ImageStudio.exe` 或 `start.bat`；没启动时脚本会明确报错）
- **技能本机零配置**：服务跑在本机时无需会员访问密钥；实际生图仍需服务端有可用的 ChatGPT 账号并配置 `image_api.engine=chatgpt`
- 远程/会员场景：配置 ImageStudio 会员访问密钥（由管理员在 设置 → 密钥 创建）；它不是 ChatGPT 账号凭证。后端需由管理员配置 ChatGPT 引擎及可用账号。

## 密钥 / 服务地址查找顺序

1. `--api-key` / `--base-url` 命令行参数
2. 环境变量 `IMAGESTUDIO_API_KEY` / `IMAGESTUDIO_BASE_URL`
3. `%USERPROFILE%\.imagestudio\config.json`（`{"base_url": "http://127.0.0.1:8020", "api_key": "<ImageStudio 会员密钥>"}`；仅远程/会员场景需填密钥）
4. 都没有 → 默认 `http://127.0.0.1:8020` 且不带密钥（本机免登录模式）

永远不要在聊天中打印密钥；仅远程服务要求鉴权时提示用户在本机写入 `%USERPROFILE%\.imagestudio\config.json`。本机免登录不必配置。

## 命令

```powershell
python "<skill-dir>\scripts\imagestudio_image_gen.py" --prompt "<提示词>" --size 1024x1024 --out "<输出.png>"
```

解析 `<skill-dir>` 为本技能目录，Windows 路径加引号。

## 工作流

1. 判断是文生图还是图生图。
2. 项目资产存到当前项目内；否则用 `output/imagestudio/`。
3. 保留用户的具体要求，只补充有用的生产性约束。
4. 运行 `scripts/imagestudio_image_gen.py`。
5. 用可用的图片查看工具检查产出图片。
6. 校验失败时做一次聚焦修正后重试。
7. 汇报输出的绝对路径与最终提示词。

除非用户明确要求，不要覆盖已存在的图片；否则使用带版本号的文件名。

## 图生图 / 多参考图

重复 `--image` 传一张或多张参考图（服务端最多 4 张）。脚本把本地文件作为 multipart 文件上传；http(s) URL 会先下载再上传。不要直接传 data URI。

```powershell
python "<skill-dir>\scripts\imagestudio_image_gen.py" `
  --prompt "只把灰色填充改成鲜绿色，保持尺寸和边框" `
  --image "D:\project\assets\progress.png" `
  --size 1024x1024 `
  --out "D:\project\assets\progress-v2.png"
```

## 常用参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--prompt` / `--prompt-file` | 必填 | 提示词（二选一） |
| `--image` | 无 | 参考图，可重复（≤4 张），走图生图 |
| `--size` | 1024x1024 | 宽x高 |
| `--n` | 1 | 生成数量 1-4（每张扣 1 次余额） |
| `--model` | 服务端默认 | 一般不用传 |
| `--timeout` | 360 | 本地服务请求超时秒数（生成通常 30–120 秒） |
| `--check` | - | 只查询会员状态（剩余天数/生图余额）与服务可用性 |

## 状态与错误

- `--check` 输出剩余天数与生图余额，生图前可用它确认额度。
- `401 密钥无效`：密钥错误或被停用。
- `401 已过期`：会员到期，到 ImageStudio 会员中心激活新密钥。
- `429 余额已用完`：生图次数用尽，联系管理员续费（管理端可一键清零或换新密钥）。
- `429 号池没有可用账号`：服务端 ChatGPT 账号不可用，联系管理员检查号池。
- `Connection refused`：ImageStudio 服务没启动。
- `503`：脚本自动指数退避重试。
- 超时：加 `--timeout 360`。
- 参考图 URL 不可达：改传本地文件路径。

不要把密钥写进聊天记录；让用户在本地配置文件里填好。
