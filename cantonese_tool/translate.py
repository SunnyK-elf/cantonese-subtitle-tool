"""粤语 → 普通话翻译：豆包（火山方舟）/ OpenAI GPT / 自定义 OpenAI 兼容接口。

自定义接口可用于：本地 ollama（完全免费、免 key）、硅基流动免费模型、
或其他任何 OpenAI 兼容服务（Groq、DeepSeek、vLLM 等）。
"""
import json
import os
import re

DOUBAO_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

SYSTEM_PROMPT = (
    "你是粤语到普通话的翻译专家。把粤语口语（粤文）翻译成自然、地道的普通话书面语。"
    "要求：1) 准确传达原意和语气；2) 恰当处理语气词（如「啦、嘅、啫、咁」），"
    "避免逐字直译的生硬感；3) 人名、地名、专有名词保留不译；4) 只输出翻译结果，不要解释。"
)

_BATCH = 100


def translate_texts(texts, provider, ark_key, openai_key, model=None,
                    custom_base_url=None, custom_key=None):
    """批量翻译，返回与 texts 等长的普通话文本列表。"""
    from openai import OpenAI

    if provider == "doubao":
        if not ark_key:
            raise RuntimeError("未设置 ARK_API_KEY（火山方舟豆包密钥）。")
        client = OpenAI(api_key=ark_key, base_url=DOUBAO_BASE_URL)
        model = model or os.getenv("ARK_MODEL_ID", "doubao-pro-32k")
    elif provider == "openai":
        if not openai_key:
            raise RuntimeError("未设置 OPENAI_API_KEY。")
        client = OpenAI(api_key=openai_key)
        model = model or os.getenv("OPENAI_MODEL_ID", "gpt-4o-mini")
    elif provider == "custom":
        if not custom_base_url:
            raise RuntimeError("自定义翻译需提供 base_url（如 http://localhost:11434/v1）。")
        if not model:
            raise RuntimeError("自定义翻译需提供 --model 模型名（如 qwen2.5:7b）。")
        client = OpenAI(api_key=custom_key or "ollama", base_url=custom_base_url)
    else:
        raise RuntimeError(f"未知翻译 provider：{provider}")

    out = []
    for i in range(0, len(texts), _BATCH):
        chunk = texts[i:i + _BATCH]
        out.extend(_translate_chunk(client, model, chunk))
        if len(texts) > _BATCH:
            print(f"  [翻译] 已完成 {min(i + _BATCH, len(texts))}/{len(texts)} 条")
    return out


def _translate_chunk(client, model, chunk):
    user = (
        "请把下面 JSON 数组中的每条粤语文本翻译成普通话，"
        "返回一个 JSON 数组，元素数量与顺序必须与输入一一对应，"
        "每条结果只包含翻译后的普通话文本字符串。\n\n"
        + json.dumps(chunk, ensure_ascii=False)
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    content = resp.choices[0].message.content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    try:
        arr = json.loads(content)
    except json.JSONDecodeError:
        arr = [ln.strip() for ln in content.splitlines() if ln.strip()]
    return arr
