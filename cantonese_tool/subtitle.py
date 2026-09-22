"""字幕工具：SRT 写出、双语合并、ASS 生成（用于烧录）。"""


def ms_to_srt(ms):
    """毫秒 → SRT 时间 'HH:MM:SS,mmm'。"""
    ms = int(ms)
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    milli = ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"


def ms_to_ass(ms):
    """毫秒 → ASS 时间 'H:MM:SS.cc'。"""
    ms = int(ms)
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    cs = (ms % 1000) // 10
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def write_srt(sentences, path):
    """sentences: [(begin_ms, end_ms, text)] → 写 SRT 文件。"""
    lines = []
    idx = 1
    for begin, end, text in sentences:
        text = (text or "").strip()
        if not text:
            continue
        lines += [str(idx), f"{ms_to_srt(begin)} --> {ms_to_srt(end)}", text, ""]
        idx += 1
    path.write_text("\n".join(lines), encoding="utf-8")
    return idx - 1


def _sanitize(text):
    """清理字幕文本中的换行与 ASS 特殊字符。"""
    return (
        (text or "")
        .replace("\r", "")
        .replace("\n", " ")
        .replace("{", "（")
        .replace("}", "）")
        .strip()
    )


def build_ass(entries, path, font="Microsoft YaHei", font_size=24, mandarin_only=False):
    """entries: [(begin_ms, end_ms, 粤语, 普通话)] → 写双语/单语 ASS 文件。

    双语布局：粤语白字在上，普通话黄字在下（用 \\N 换行 + 内联颜色）。
    """
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1920\n"
        "PlayResY: 1080\n"
        "ScaledBorderAndShadow: yes\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
        "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{font},{font_size},&H00FFFFFF,&H000000FF,"
        "&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,30,30,40,1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = [header]
    for begin, end, yue, zh in entries:
        if mandarin_only:
            text = _sanitize(zh)
        else:
            text = _sanitize(yue) + r"\N" + r"{\c&H0000FFFF&}" + _sanitize(zh)
        lines.append(
            f"Dialogue: 0,{ms_to_ass(begin)},{ms_to_ass(end)},Default,,0,0,0,,{text}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
