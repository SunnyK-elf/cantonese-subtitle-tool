"""本地免费粤语识别：faster-whisper（whisper 模型，language=yue）。

无需 API Key、可完全离线，识别结果自带句子级时间戳，直接转 SRT。
依赖（可选，见 requirements-local.txt）：`pip install faster-whisper`
"""
import os
from pathlib import Path


def transcribe_local(audio_path, model_dir="models", model_size="medium", language="yue"):
    """本地转写，返回 [(begin_ms, end_ms, text), ...]。

    model_dir：模型缓存目录，模型会下载到这里（默认本工具目录下的 models/，
    避免写入用户 C 盘默认缓存）。
    model_size：whisper 模型档位，tiny/base/small/medium/large-v3。
    """
    model_dir = str(Path(model_dir).resolve())

    # 关键：把 HuggingFace 缓存重定向到本地模型目录，避免写 C 盘 ~/.cache/huggingface
    os.environ.setdefault("HF_HOME", model_dir)
    os.environ.setdefault("HF_HUB_CACHE", os.path.join(model_dir, "hub"))

    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise RuntimeError(
            "本地识别需要 faster-whisper：请先 `pip install faster-whisper`，"
            "或改用云端识别（--asr-engine cloud）。"
        ) from e

    # int8 量化：CPU 也能较快运行；有 GPU 会自动用 GPU
    model = WhisperModel(model_size, device="auto", compute_type="int8", download_root=model_dir)
    segments, _info = model.transcribe(
        str(audio_path),
        language=language,
        beam_size=5,
        vad_filter=True,
    )

    out = []
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        out.append((int(seg.start * 1000), int(seg.end * 1000), text))
    return out
