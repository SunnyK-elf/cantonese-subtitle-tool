#!/usr/bin/env python3
"""粤语视频字幕识别 + 翻译 + 烧录 —— 命令行入口。

用法示例：
    python main.py 视频.mp4
    python main.py 视频.mp4 --provider openai --font "SimHei"
    python main.py 音频.m4a --no-burn        # 只出 srt，不烧录

图形界面请运行：python gui.py
"""
from cantonese_tool.cli import main

if __name__ == "__main__":
    main()
