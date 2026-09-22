"""粤语语音识别：阿里云百炼 Paraformer（paraformer-mtl-v1，支持粤语）。

返回句子级结果 [(begin_ms, end_ms, text), ...]。
"""
import json
import time
import urllib.request

MODEL = "paraformer-mtl-v1"


def transcribe(audio_path, api_key, model=MODEL):
    """提交异步转写任务并轮询结果，返回 [(begin_ms, end_ms, text)]。"""
    import dashscope
    from dashscope.audio.asr import Transcription

    dashscope.api_key = api_key

    src = str(audio_path.resolve())
    print(f"  [识别] 模型 {model}，提交任务……")
    try:
        task = Transcription.async_call(model=model, file_urls=[src])
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"识别任务提交失败：{exc}\n"
            "提示：file_urls 需公网可访问 URL。若本地路径无法被 SDK 自动上传，"
            "请先把音频上传到 OSS/公网地址后，用该 URL 重试。"
        ) from exc

    task_id = task.output.task_id
    print(f"  [识别] 任务 ID：{task_id}")

    resp = Transcription.fetch(task=task_id)
    status = resp.output.task_status
    while status in ("PENDING", "RUNNING"):
        time.sleep(5)
        resp = Transcription.fetch(task=task_id)
        status = resp.output.task_status
        print(f"  [识别] 状态：{status}")

    if status != "SUCCEEDED":
        raise RuntimeError(f"识别失败，任务状态：{status}")

    sentences = list(_extract_sentences(resp.output))
    if not sentences:
        raise RuntimeError("识别完成但未得到任何句子，请检查音频内容。")
    return sentences


def _extract_sentences(output):
    """兼容新旧两种结果格式，逐条产出 (begin_ms, end_ms, text)。"""
    for r in output.get("results") or []:
        url = r.get("transcription_url")
        if url:  # 新格式：结果在 transcription_url 指向的文件里
            data = _fetch_json(url)
            for t in data.get("transcripts", []):
                for s in t.get("sentences", []):
                    yield int(s["begin_time"]), int(s["end_time"]), s["text"].strip()
        for t in r.get("transcripts", []):  # 旧格式：内联
            for s in t.get("sentences", []):
                yield int(s["begin_time"]), int(s["end_time"]), s["text"].strip()


def _fetch_json(url):
    with urllib.request.urlopen(url, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))
