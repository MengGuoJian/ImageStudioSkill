# ImageStudio Skill（鱼舟生图 · 智能体生图技能）

让 ZCode / Codex 等智能体安装后即可调用 [ImageStudio（鱼舟生图）](https://github.com/MengGuoJian/FishImagen) 的 API 生图：
文生图、图生图（多参考图）、会员额度查询。服务端自动做号池 key 轮询与额度扣减，智能体侧零心智。

## 安装

**方式一（推荐）：git clone 到智能体技能目录**

```powershell
git clone https://github.com/MengGuoJian/ImageStudioSkill.git "%USERPROFILE%\.agents\skills\imagestudio"
```

**方式二：下载后运行 install.bat**（把本目录拷贝到 `%USERPROFILE%\.agents\skills\imagestudio`）

前置：本机有 Python 3.9+（脚本只依赖标准库）。

## 使用前提

- ImageStudio 服务已启动（双击 `ImageStudio.exe` 或 `start.bat`）
- **本机使用零配置**——服务跑在本机时无需任何密钥，安装即可用
- 远程/会员场景：在 `%USERPROFILE%\.imagestudio\config.json` 配置 `{"base_url": "服务地址", "api_key": "sk-会员密钥"}`

## 智能体用法（SKILL.md 自动生效）

```powershell
# 文生图
python "%USERPROFILE%\.agents\skills\imagestudio\scripts\imagestudio_image_gen.py" --prompt "一只戴围巾的橘猫" --size 1024x1024 --out out.png

# 图生图（参考图最多 4 张）
python "...imagestudio_image_gen.py" --prompt "把背景换成海边日落" --image ref.png --out out-v2.png

# 查询剩余天数 / 生图余额
python "...imagestudio_image_gen.py" --check
```

参数详见 [SKILL.md](SKILL.md)。
