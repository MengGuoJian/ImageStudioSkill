# ImageStudio Skill（鱼舟生图 · 智能体生图技能）

让 ZCode / Codex / Claude 等智能体安装后即可调用 [ImageStudio（鱼舟生图）](https://github.com/MengGuoJian/FishImagen) 的本地/自建服务接口生图：
文生图、图生图（多参考图）、会员额度查询。ImageStudio 服务端配置 ChatGPT 生图引擎并管理账号池；技能只调用 ImageStudio 的 `/v1/images/*`，不直连 ChatGPT 或其他上游 API。

**技能本机零配置**：启动 ImageStudio 服务并确保账号池与剩余生图额度可用后，技能在本机无需再配置访问密钥。

---

## 一、安装教程

**方式一（推荐）：git clone 到智能体技能目录**

```powershell
git clone https://github.com/MengGuoJian/ImageStudioSkill.git "$env:USERPROFILE\.agents\skills\imagestudio"
```

**方式二：下载 zip 后运行 install.bat**（自动拷贝到 `%USERPROFILE%\.agents\skills\imagestudio`）

前置：本机有 Python 3.10+（脚本只依赖标准库，无需 pip 装任何东西）。

装完重启智能体会话即可；SKILL.md 里有完整的触发词与工作流，智能体会自动按它执行。

## 二、配置教程（可选）

| 场景 | 需要配置吗 |
|---|---|
| ImageStudio 跑在本机（默认 `http://127.0.0.1:8020`） | **不需要，装完即用** |
| 服务在别的机器 / 远程访问需鉴权 | 配置 ImageStudio 服务地址和会员访问密钥；不要填 ChatGPT 账号凭证 |

配置方法（三选一）：

1. 配置文件 `%USERPROFILE%\.imagestudio\config.json`：

   ```json
   {
     "base_url": "http://192.168.1.100:8020",
     "api_key": "<你的 ImageStudio 会员密钥>"
   }
   ```

2. 环境变量：`IMAGESTUDIO_BASE_URL`、`IMAGESTUDIO_API_KEY`
3. 命令行参数：`--base-url`、`--api-key`

优先级：命令行 > 环境变量 > 配置文件 > 默认本机 8020。这里的 `base_url` 是 ImageStudio 服务地址，不是 ChatGPT 上游地址。`api_key` 是访问 ImageStudio 的会员密钥，本机免登录可省略；ChatGPT 账号由管理员在服务端配置。不要在聊天中提供真实密钥。

## 三、使用教程

PowerShell 示例先设置 `$skillScript` 为技能脚本路径（安装到其他位置时相应修改）：

```powershell
$skillScript = "$env:USERPROFILE\.agents\skills\imagestudio\scripts\imagestudio_image_gen.py"
```

### 1. 文生图

```powershell
python $skillScript --prompt "一只戴围巾的橘猫，坐在窗边，柔光，胶片质感" --size 1024x1024 --out out.png
```

### 2. 图生图（参考图）

`--image` 可重复传最多 4 张；本地文件走 multipart 上传，http(s) URL 由脚本先下载再上传（不直接传 data URI）：

```powershell
python $skillScript --prompt "把背景换成海边日落，保持主体不变" --image ref1.png --image ref2.png --out out-v2.png
```

### 3. 一次生成多张

```powershell
python $skillScript --prompt "赛博朋克城市夜景" --n 4 --out sheet.png
# 输出 sheet.png / sheet-2.png / sheet-3.png / sheet-4.png，每张扣 1 次额度
```

### 4. 查询会员额度

```powershell
python $skillScript --check
# 服务地址: http://127.0.0.1:8020
# 身份: 张三 · 剩余 30 天 · 生图余额 87 次
```

### 参数速查

| 参数 | 默认 | 说明 |
|---|---|---|
| `--prompt` / `--prompt-file` | 必填 | 提示词（二选一） |
| `--image` | 无 | 本地参考图路径或 http(s) URL，可重复（≤4 张） |
| `--size` | 1024x1024 | 宽x高 |
| `--n` | 1 | 数量 1–4 |
| `--model` | 服务端默认 | 一般不用传 |
| `--out` | output/imagestudio/image.png | 输出路径 |
| `--timeout` | 360 | 单张超时秒数 |
| `--check` | - | 只查额度/天数 |

## 四、错误对照

| 报错 | 含义 | 解决 |
|---|---|---|
| 无法连接 ImageStudio 服务 | 服务没启动 | 双击 `ImageStudio.exe` / `start.bat` |
| 密钥无效或已被停用 | key 错了 / 停用 | 核对密钥；本机使用可不配置密钥 |
| 会员密钥已过期 | 天数用完 | 到会员中心激活新密钥 |
| 生图余额已用完 | 次数用完 | 联系运营商续费 |
| 号池没有可用账号 | 服务端 ChatGPT 账号不可用 | 联系管理员检查账号池 |
| 503 | 服务暂时不可用 | 脚本已自动退避重试，再试一次 |

## 五、FAQ

- **生图要多久？** 正常 30–120 秒；超时可加 `--timeout 600`。
- **输出在哪？** `--out` 指定的路径；不指定则存到 `output/imagestudio/`。
- **额度怎么扣？** 每成功生成一张扣 1 次；失败不扣。服务端自动扣，智能体无需关心。
- **不要覆盖已有图？** 脚本可能覆盖 `--out` 指定的现有文件；先选一个不存在的版本号文件名。一次多张时后续图片自动加 -2/-3 后缀。

## 六、给智能体的提示

`SKILL.md` 即技能定义（含触发词、工作流、错误处理约定）。本仓库根目录就是技能目录结构，
clone 到技能目录后无需任何改动。ImageStudio 主项目与完整文档见
[FishImagen](https://github.com/MengGuoJian/FishImagen)。
