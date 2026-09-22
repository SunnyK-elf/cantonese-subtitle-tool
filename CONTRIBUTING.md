# 参与贡献

感谢你想为这个项目做贡献！欢迎提交 Issue 和 Pull Request。

## 开发环境

```bash
git clone https://github.com/SunnyK-elf/cantonese-subtitle-tool.git
cd cantonese-subtitle-tool
pip install -r requirements.txt
```

## 目录结构

```
main.py                  # 命令行入口（薄封装）
gui.py                   # 图形界面入口
cantonese_tool/
├── cli.py               # 命令行逻辑
├── pipeline.py          # 核心流水线（CLI 与 GUI 共用）
├── asr.py               # 阿里云 Paraformer 粤语识别
├── translate.py         # 豆包/GPT 翻译
├── subtitle.py          # SRT 写出 + 双语 ASS 生成
├── audio.py             # 音频抽取 + ffmpeg 定位
├── burn.py              # ffmpeg 烧录
└── config.py            # 配置读取
```

## 提交规范

- 一个 PR 只做一件事，写清楚动机和改动点。
- 涉及行为改动请补充说明，复杂逻辑尽量加注释。
- 不要在 PR 里提交密钥（`.env`、`config.json` 已在 `.gitignore` 中忽略）。

## 构建 exe（可选）

```bash
pip install pyinstaller
# 把 ffmpeg.exe 放到 bin/ 目录后：
pyinstaller --noconfirm --clean --onefile --windowed --name "cantonese-subtitle-tool" --add-binary "bin/ffmpeg.exe;bin" gui.py
```

输出在 `dist/cantonese-subtitle-tool.exe`。
