# ImageStudio Skill（鱼舟生图 · 智能体生图技能）

让 ZCode / Codex / Claude 等智能体安装后即可调用 [ImageStudio（鱼舟生图）](https://github.com/MengGuoJian/FishImagen) 的 API 生图：
文生图、图生图（多参考图）、会员额度查询。服务端自动做号池 key 轮询与额度扣减，智能体侧零心智。

**本机使用零配置**：只要 ImageStudio 服务在本机运行，装完就能画。

---

## 一、安装教程

**方式一（推荐）：git clone 到智能体技能目录**

```powershell
git clone https://github.com/MengGuoJian/ImageStudioSkill.git "%USERPROFILE%\.agents\skills\imagestudio"
```

**方式二：下载 zip 后运行 install.bat**（自动拷贝到 `%USERPROFILE%\.agents\skills\imagestudio`）

前置：本机有 Python 3.9+（脚本只依赖标准库，无需 pip 装任何东西）。

装完重启智能体会话即可；SKILL.md 里有完整的触发词与工作流，智能体会自动按它执行。

## 二、配置教程（可选）

| 场景 | 需要配置吗 |
|---|---|
| ImageStudio 跑在本机（默认 `http://127.0.0.1:8020`） | **不需要，装完即用** |
| 服务在别的机器 / 你是购买额度的会员 | 需要配置服务地址 + 会员密钥 |

配置方法（三选一）：

1. 配置文件 `%USERPROFILE%\.imagestudio\config.json`：

   ```json
   {
     "base_url": "http://192.168.1.100:8020",
     "api_key": "sk-你的会员密钥"
   }
   ```

2. 环境变量：`IMAGESTUDIO_BASE_URL`、`IMAGESTUDIO_API_KEY`
3. 命令行参数：`--base-url`、`--api-key`

优先级：命令行 > 环境变量 > 配置文件 > 默认本机 8020。

## 三、使用教程

脚本路径以下简写为 `%SKILL%` = `%USERPROFILE%\.agents\skills\imagestudio\scripts\imagestudio_image_gen.py`。

### 1. 文生图

```powershell
python "%SKILL%" --prompt "一只戴围巾的橘猫，坐在窗边，柔光，胶片质感" --size 1024x1024 --out out.png
```

### 2. 图生图（参考图）

`--image` 可重复传最多 4 张，本地文件自动转 base64 上传：

```powershell
python "%SKILL%" --prompt "把背景换成海边日落，保持主体不变" --image ref1.png --image ref2.png --out out-v2.png
```

### 3. 一次生成多张

```powershell
python "%SKILL%" --prompt "赛博朋克城市夜景" --n 4 --out sheet.png
# 输出 sheet.png / sheet-2.png / sheet-3.png / sheet-4.png，每张扣 1 次额度
```

### 4. 查询会员额度

```powershell
python "%SKILL%" --check
# 服务地址: http://127.0.0.1:8020
# 身份: 张三 · 剩余 30 天 · 生图余额 87 次
```

### 参数速查

| 参数 | 默认 | 说明 |
|---|---|---|
| `--prompt` / `--prompt-file` | 必填 | 提示词（二选一） |
| `--image` | 无 | 参考图路径/URL，可重复（≤4 张） |
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
| 号池没有可用 key | 站长侧上游耗尽 | 联系运营商补充 |
| 503 | 上游抖动 | 脚本已自动退避重试，再试一次 |

## 五、FAQ

- **生图要多久？** 正常 30–120 秒；超时可加 `--timeout 600`。
- **输出在哪？** `--out` 指定的路径；不指定则存到 `output/imagestudio/`。
- **额度怎么扣？** 每成功生成一张扣 1 次；失败不扣。服务端自动扣，智能体无需关心。
- **不要覆盖已有图？** 脚本不会自动覆盖同名文件（多张时自动加 -2/-3 后缀），智能体侧也约定用版本号文件名。

## 六、给智能体的提示

`SKILL.md` 即技能定义（含触发词、工作流、错误处理约定）。本仓库根目录就是技能目录结构，
clone 到技能目录后无需任何改动。ImageStudio 主项目与完整文档见
[FishImagen](https://github.com/MengGuoJian/FishImagen)。
