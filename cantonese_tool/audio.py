"""音频抽取：用 ffmpeg 把视频/音频统一转成 16kHz 单声道 wav。"""
import shutil
import subprocess
import sys
from pathlib import Path


class FFmpegNotFound(RuntimeError):
    pass


def find_ffmpeg() -> str:
    """返回可用的 ffmpeg 可执行路径。

    查找顺序：
    1. PATH 中的 ffmpeg；
    2. PyInstaller 打包后解压目录（``sys._MEIPASS/bin``）；
    3. 随工具一起分发的 ``bin/ffmpeg.exe``（Windows）/ ``bin/ffmpeg``。
    """
    exe = shutil.which("ffmpeg")
    if exe:
        return exe

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        cand = Path(meipass) / "bin" / "ffmpeg.exe"
        if cand.exists():
            return str(cand)

    bin_dir = Path(__file__).resolve().parent.parent / "bin"
    for name in ("ffmpeg.exe", "ffmpeg"):
        cand = bin_dir / name
        if cand.exists():
            return str(cand)

    raise FFmpegNotFound(
        "未检测到 ffmpeg。请任选其一：\n"
        "  1) 把 ffmpeg.exe 放到工具目录的 bin/ 文件夹下（推荐，随工具分发）；\n"
        "  2) 安装到系统 PATH：Windows `winget install Gyan.FFmpeg`，"
        "macOS `brew install ffmpeg`，Linux `sudo apt install ffmpeg`。"
    )


def require_ffmpeg():
    find_ffmpeg()


def extract_audio(input_path, output_wav: Path):
    """把视频或音频转成 16kHz 单声道 wav（Paraformer 最优输入）。

    对音频输入，-vn 只是忽略视频流，结果一致；因此视频/音频可共用本函数。
    """
    ffmpeg = find_ffmpeg()
    cmd = [
        ffmpeg, "-y",
        "-i", str(input_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-f", "wav",
        str(output_wav),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 抽取音频失败：{proc.stderr.strip()}")
    return output_wav
