"""字幕烧录：用 ffmpeg 把 ASS 字幕硬编码进视频。"""
import subprocess
from pathlib import Path

from .audio import find_ffmpeg


def burn_subtitles(video_path, ass_path: Path, output_path: Path):
    """把 ass_path 的字幕烧录进视频，输出到 output_path。

    在 ass 所在目录下运行、按纯文件名引用，规避 Windows 路径中
    ':' 和 '\\' 在 ffmpeg 滤镜里的转义问题。
    """
    ffmpeg = find_ffmpeg()
    cmd = [
        ffmpeg, "-y",
        "-i", str(video_path),
        "-vf", f"ass={ass_path.name}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(output_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ass_path.parent))
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 烧录字幕失败：{proc.stderr.strip()}")
    return output_path
