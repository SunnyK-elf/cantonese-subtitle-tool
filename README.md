# 粤语字幕工具（Cantonese Subtitle Tool）

把粤语视频/音频**自动识别**出粤语字幕，**翻译**成普通话，并**烧录**成双语字幕视频。一条命令搞定，下载即用。

```
粤语视频 ──► 抽音频 ──► 粤语识别(阿里云 Paraformer) ──► 翻译(豆包/GPT) ──► 烧录(ffmpeg)
                    │                                     │
                    └──── 粤语.srt ────────────────────────┴──── 普通话.srt / 双语.srt
```

## 快速上手（三种方式任选）

**① 下载打包好的 exe —— 最省事，无需装 Python/ffmpeg**

到 [Releases](https://github.com/SunnyK-elf/cantonese-subtitle-tool/releases) 下载 `cantonese-subtitle-tool.exe`，双击即用（ffmpeg 已内置）。

**② pip 安装 —— 命令行爱好者**

```bash
pip install git+https://github.com/SunnyK-elf/cantonese-subtitle-tool.git
cantonese-subtitle 视频.mp4          # 需自行安装 ffmpeg
```

**③ 从源码运行**

```bash
git clone https://github.com/SunnyK-elf/cantonese-subtitle-tool.git
cd cantonese-subtitle-tool
pip install -r requirements.txt
python gui.py             # 图形界面
python main.py 视频.mp4   # 或命令行
```

> 识别与翻译都有「免费本地」选项（见下方），云端方式才需要密钥。默认走云（新用户有免费额度）。

## 功能特性

- 🎬 **输入视频或音频**：mp4 / mkv / mov 等视频，mp3 / wav / m4a 等音频都行
- 🗣️ **粤语语音识别**：阿里云百炼 Paraformer（`paraformer-mtl-v1`，原生支持粤语）
- 🆓 **本地免费识别（可选）**：faster-whisper（whisper 模型，粤语），无需 key、可离线
- 🌐 **粤语→普通话翻译**：豆包 / GPT / 自定义接口（本地 ollama、硅基流动等），可切换
- 🎞️ **双语字幕烧录**：把「粤语（白字）+ 普通话（黄字）」硬编码进视频，输出成品视频
- 📄 **同时保留字幕文件**：粤语.srt、普通话.srt、双语.srt 一并输出

## 🆓 免费本地识别（不想注册云服务？）

识别这一步可以**完全免费、免 key**：切换到本地 faster-whisper（whisper 模型），无需注册任何云账号。

```bash
# 1) 安装本地识别依赖（一次性，比云 SDK 轻量）
pip install -r requirements-local.txt

# 2) 用本地引擎识别（首次自动下载模型，约 1.5GB，存到本工具 models/ 目录，不写 C 盘缓存）
python main.py 视频.mp4 --asr-engine local
```

图形界面里，把「识别」从「云端」切到「本地（免费，免 key）」即可。

- **优点**：识别免费、免 key、可离线、模型存本工具目录（不碰 C 盘）
- **代价**：首次需下载模型约 1.5GB（`--model-size` 可选 `tiny/base/small/medium/large-v3`，越小越快越省、越大越准）；粤语准确度略低于云端 Paraformer
- **翻译**也可以免费，见下一节

## 🆓 免费翻译（翻译也能不要钱）

翻译同样支持**完全免费**，走「自定义 OpenAI 兼容接口」，两种免费姿势任选：

**① 本地 ollama（彻底免费、离线、免 key）**

```bash
# 先到 https://ollama.com 下载安装 ollama，拉一个小模型（一次性）
ollama pull qwen2.5:7b

# 翻译指向本地
python main.py 视频.mp4 --provider custom --base-url http://localhost:11434/v1 --model qwen2.5:7b
```

**② 硅基流动免费模型（有免费额度，国内直连）**

```bash
# 到 siliconflow.cn 注册，免费拿一个 API Key，然后：
python main.py 视频.mp4 --provider custom \
    --base-url https://api.siliconflow.cn/v1 \
    --model Qwen/Qwen2.5-7B-Instruct \
    --custom-key 你的key
```

图形界面里，把「翻译」选「自定义」，填上「接口地址 / 模型名 / key」即可（ollama 的 key 留空）。

> 小提醒：本地小模型（7B）翻粤语口语的**质量会明显不如**豆包/GPT 这类大模型，专名、俚语容易翻错。免费和质量是取舍——要省事又准，还是推荐豆包（token 很便宜）。

## 🖥️ 图形界面（推荐，最省事）

不用记命令，双击就能用：

```bash
# 第一次：装依赖（只需一次）
install.bat            # Windows 双击；macOS/Linux 用 pip install -r requirements.txt

# 每次使用：双击启动图形界面
start_gui.bat          # Windows 双击；macOS/Linux 用 python gui.py
```

打开后的界面里：

1. **选择文件** 点一下，挑你的视频/音频
2. **密钥设置** 点一下，粘贴阿里云百炼 + 豆包/GPT 的 Key（保存一次，以后免填）
3. **开始处理** 点一下，看进度条跑完
4. 完成后自动提示打开输出文件夹

> GUI 也支持命令行方式（`python gui.py`），所有参数在界面上点选即可，无需记忆。

## 环境要求

| 依赖 | 说明 |
|------|------|
| Python 3.8+ | 运行脚本 |
| ffmpeg | 抽音频 + 烧录字幕。**Windows**：`winget install Gyan.FFmpeg`；**macOS**：`brew install ffmpeg`；**Linux**：`sudo apt install ffmpeg` |
| 阿里云百炼 API Key | 云端粤语识别（选「本地识别」则可不用） |
| 豆包 / OpenAI / 自定义 API Key | 翻译（自定义可接本地 ollama、硅基流动等，见「免费翻译」） |
| faster-whisper（可选） | 本地免费识别，`pip install -r requirements-local.txt` |

## 给开发者：自动打包发布 exe

项目内置了 GitHub Actions（`.github/workflows/release.yml`）。给仓库打一个 `v` 开头的 tag（如 `v1.0.0`）并推送，GitHub 会自动：

1. 在云端 Windows 环境下载静态 ffmpeg；
2. 用 PyInstaller 把图形界面打成单个 `cantonese-subtitle-tool.exe`（内置 ffmpeg）；
3. 发布到该 tag 的 Release 页面。

之后其他用户就能从 Release 下载 exe、双击即用，无需装 Python 和 ffmpeg。

## 配置（密钥）

**图形界面版**：启动后点「密钥设置」，在弹窗里粘贴即可，保存到本目录 `config.json`，下次免填，**不用改任何文件**。

**命令行版**才需要 `.env`：

```bash
cp .env.example .env      # Windows: copy .env.example .env
```

编辑 `.env`：

```ini
DASHSCOPE_API_KEY=sk-xxxxxxxx        # 阿里云百炼（粤语识别）
ARK_API_KEY=xxxxxxxx                 # 火山方舟豆包（翻译，--provider doubao）
# OPENAI_API_KEY=sk-xxxxxxxx         # 或 OpenAI（翻译，--provider openai）
# CUSTOM_BASE_URL=http://localhost:11434/v1   # 自定义翻译（本地 ollama 免费）
# CUSTOM_API_KEY=                             # 自定义翻译 key（ollama 可留空）
```

> 密钥获取：阿里云百炼 https://bailian.console.aliyun.com/ ；火山方舟 https://console.volcengine.com/ark 。
> 两者新用户均有免费额度，超过后按量计费（识别约按音频分钟、翻译按 token）。

## 快速开始

```bash
# 视频输入 → 输出双语字幕视频 + 三个 srt
python main.py 我的粤语视频.mp4

# 指定输出目录
python main.py 我的粤语视频.mp4 -o out

# 音频输入（只出字幕，无法烧录进视频）
python main.py 粤语录音.m4a

# 用 GPT 翻译
python main.py 视频.mp4 --provider openai

# 本地免费识别（免 key，首次自动下载模型到 models/）
python main.py 视频.mp4 --asr-engine local

# 只烧普通话、不要粤语行
python main.py 视频.mp4 --mandarin-only

# 只生成 srt，不烧录
python main.py 视频.mp4 --no-burn

# 自定义字体/字号（避免中文字体显示为方块时很有用）
python main.py 视频.mp4 --font "SimHei" --font-size 28
```

Windows 用户也可双击 `run.bat`，或在命令行 `run.bat 视频.mp4`。

## 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `input` | — | 输入视频/音频文件路径（必填） |
| `-o, --output` | `output` | 输出目录 |
| `--provider` | `doubao` | 翻译：`doubao` / `openai` / `custom`（自定义 OpenAI 兼容接口） |
| `--base-url` | — | 自定义翻译接口地址（`custom` 时用，如 http://localhost:11434/v1） |
| `--custom-key` | — | 自定义翻译接口密钥（本地 ollama 可留空） |
| `--asr-engine` | `cloud` | 识别引擎：`cloud`（阿里云）或 `local`（本地免费） |
| `--model-dir` | `models` | 本地识别模型缓存目录（不写 C 盘缓存） |
| `--model-size` | `medium` | 本地识别 whisper 档位（tiny/base/small/medium/large-v3） |
| `--mandarin-only` | 关 | 只烧普通话字幕（默认双语） |
| `--no-burn` | 关 | 只生成 srt，不烧录 |
| `--font` | `Microsoft YaHei` | 字幕字体 |
| `--font-size` | `24` | 字幕字号 |
| `--model` | — | 翻译模型 ID 覆盖 |
| `--keep-temp` | 关 | 保留中间音频 |

## 输出文件

以 `我的粤语视频.mp4` 为例，输出目录下会生成：

```
output/
├── 我的粤语视频.粤语.srt      # 识别出的粤语字幕
├── 我的粤语视频.普通话.srt    # 翻译后的普通话字幕
├── 我的粤语视频.双语.srt      # 双语对照字幕
├── 我的粤语视频.双语.ass      # 烧录用的样式字幕
└── 我的粤语视频_字幕版.mp4    # 烧录好的成品视频
```

音频输入时输出前三个 srt + `xxx.全文.txt`（无成品视频）。

## 工作原理

1. **抽音频**：ffmpeg 把视频/音频转成 16kHz 单声道 wav（识别最优输入）
2. **粤语识别**：云端用阿里云 Paraformer `paraformer-mtl-v1`，或本地用 faster-whisper（whisper 模型，`language=yue`），返回带时间戳的粤语文本
3. **翻译**：把粤语文本批量交给豆包/GPT 或自定义接口（本地 ollama、硅基流动等）翻译成普通话，逐条保持时间轴
4. **烧录**：生成双语 ASS 字幕，用 ffmpeg 硬编码进视频（重新编码视频、音频直接复制）

## 常见问题

**Q：字幕里的中文显示成方块？**
A：是烧录时字体没找到。用 `--font` 指定一个本机有的中文字体，如 `SimHei`（黑体）、`Microsoft YaHei`（微软雅黑）、`SimSun`（宋体）。

**Q：识别提交失败，提示需要 URL？**
A：阿里云文件转写接口要求音频可公网访问。多数新版 SDK 会自动上传本地文件；若失败，请先把音频传到 OSS 等可访问地址，再传 URL。

**Q：识别不准怎么办？**
A：`paraformer-mtl-v1` 是通用方言模型，粤语口语的专名、俚语可能出错。可改用质量更高的识别服务，或对生成的 `.粤语.srt` 人工校对后再翻译。

**Q：烧录很慢？**
A：烧录需重新编码视频。可接受时用更快 preset（改 `burn.py` 中 `-preset`），或加 `--no-burn` 只出字幕、用播放器外挂加载。

## License

[MIT](./LICENSE)
