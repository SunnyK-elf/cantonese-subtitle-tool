"""核心流水线：视频/音频 → 抽音频 → 粤语识别 → 翻译 → 双语字幕烧录。

被 CLI（main.py）和 GUI（gui.py）共用，通过 ``log`` 回调上报进度。
"""
from pathlib import Path

from . import asr, audio, burn, local_asr, subtitle
from .translate import translate_texts

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".flv", ".webm", ".m4v", ".ts", ".wmv", ".mpg", ".mpeg"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma", ".amr"}


def run(
    input_path,
    output_dir="output",
    provider="doubao",
    mandarin_only=False,
    no_burn=False,
    font="Microsoft YaHei",
    font_size=24,
    model=None,
    keep_temp=False,
    asr_engine="cloud",
    model_dir="models",
    model_size="medium",
    dashscope_key=None,
    ark_key=None,
    openai_key=None,
    custom_base_url=None,
    custom_key=None,
    log=print,
):
    """执行完整流水线，返回输出文件清单（list[Path]）。

    抛出的异常均为带中文说明的 RuntimeError，可直接展示给用户。
    """
    src = Path(input_path)
    if not src.exists():
        raise RuntimeError(f"文件不存在：{src}")

    ext = src.suffix.lower()
    is_audio = ext in AUDIO_EXTS
    is_video = ext in VIDEO_EXTS or not is_audio  # 未知扩展名默认当视频

    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    stem = src.stem
    outputs = []

    # ---- 1. 抽取音频 ----
    log("[1/4] 抽取音频（16kHz 单声道 wav）……")
    tmp_wav = outdir / f"{stem}.temp.wav" if not keep_temp else outdir / f"{stem}.wav"
    audio.extract_audio(src, tmp_wav)

    # ---- 2. 粤语识别 ----
    if asr_engine == "local":
        log(f"[2/4] 粤语语音识别（本地 faster-whisper，免费，模型 {model_size}）……")
        sentences = local_asr.transcribe_local(tmp_wav, model_dir, model_size)
    else:
        log("[2/4] 粤语语音识别（阿里云 Paraformer）……")
        sentences = asr.transcribe(tmp_wav, dashscope_key)
    yue_texts = [s[2] for s in sentences]
    log(f"  [识别] 共 {len(sentences)} 句")

    # ---- 3. 翻译 ----
    log(f"[3/4] 翻译成普通话（provider={provider}）……")
    zh_texts = translate_texts(yue_texts, provider, ark_key, openai_key, model, custom_base_url, custom_key)
    if len(zh_texts) < len(sentences):
        log(f"  警告：翻译结果 {len(zh_texts)} 条 < 原文 {len(sentences)} 条，缺失部分保留原文。")
        zh_texts += yue_texts[len(zh_texts):]
    zh_texts = zh_texts[: len(sentences)]

    # ---- 写出 srt ----
    yue_srt = outdir / f"{stem}.粤语.srt"
    zh_srt = outdir / f"{stem}.普通话.srt"
    bi_srt = outdir / f"{stem}.双语.srt"
    subtitle.write_srt(sentences, yue_srt)
    subtitle.write_srt([(b, e, z) for (b, e, _), z in zip(sentences, zh_texts)], zh_srt)
    combined = [(b, e, y, z) for (b, e, y), z in zip(sentences, zh_texts)]
    subtitle.write_srt([(b, e, f"{y}\n{z}") for b, e, y, z in combined], bi_srt)
    outputs += [yue_srt, zh_srt, bi_srt]

    # ---- 4. 烧录 ----
    if is_video and not no_burn:
        log("[4/4] 合成双语字幕到视频（需重新编码，稍等）……")
        ass_path = outdir / f"{stem}.双语.ass"
        subtitle.build_ass(combined, ass_path, font, font_size, mandarin_only)
        out_video = outdir / f"{stem}_字幕版.mp4"
        burn.burn_subtitles(src, ass_path, out_video)
        outputs.append(out_video)
        log(f"  完成！输出视频：{out_video}")
    elif is_audio:
        log("[4/4] 输入为音频，跳过烧录；另生成纯文本翻译稿。")
        txt_path = outdir / f"{stem}.全文.txt"
        txt_path.write_text("\n".join(f"{y}\t{z}" for _, _, y, z in combined), encoding="utf-8")
        outputs.append(txt_path)
    else:
        log("[4/4] 已按 no_burn 跳过烧录，仅输出 srt。")

    # ---- 清理临时音频 ----
    if not keep_temp:
        tmp_wav.unlink(missing_ok=True)

    return outputs
