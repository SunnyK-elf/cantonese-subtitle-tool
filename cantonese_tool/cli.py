"""命令行入口（供 ``cantonese-subtitle`` 命令与 ``python main.py`` 共用）。"""
import argparse
import sys
from pathlib import Path

from . import config, pipeline


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="cantonese-subtitle",
        description="粤语视频/音频 → 识别粤语字幕 → 翻译普通话 → 烧录双语字幕",
    )
    p.add_argument("input", help="输入视频或音频文件路径")
    p.add_argument("-o", "--output", default="output", help="输出目录（默认 ./output）")
    p.add_argument("--provider", choices=["doubao", "openai", "custom"], default="doubao",
                   help="翻译模型：doubao（默认）/ openai / custom（自定义 OpenAI 兼容接口，如本地 ollama、硅基流动免费模型）")
    p.add_argument("--base-url", help="自定义翻译接口地址（--provider custom 时必填，如 http://localhost:11434/v1）")
    p.add_argument("--custom-key", help="自定义翻译接口密钥（本地 ollama 可省略，填任意值）")
    p.add_argument("--asr-engine", choices=["cloud", "local"], default="cloud",
                   help="识别引擎：cloud=阿里云（默认），local=本地 faster-whisper（免费、免 key）")
    p.add_argument("--model-dir", default="models", help="本地识别模型缓存目录（默认 ./models，不写 C 盘缓存）")
    p.add_argument("--model-size", default="medium", help="本地识别 whisper 模型档位（tiny/base/small/medium/large-v3）")
    p.add_argument("--mandarin-only", action="store_true", help="只烧录普通话字幕（默认双语）")
    p.add_argument("--no-burn", action="store_true", help="只生成 srt，不烧录进视频")
    p.add_argument("--font", default="Microsoft YaHei", help="字幕字体（默认 Microsoft YaHei）")
    p.add_argument("--font-size", type=int, default=24, help="字幕字号（默认 24）")
    p.add_argument("--model", help="翻译模型 ID 覆盖（如 doubao-pro-32k / gpt-4o-mini）")
    p.add_argument("--keep-temp", action="store_true", help="保留中间音频文件")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    cfg = config.load_config()

    missing = []
    if args.asr_engine == "cloud" and not cfg["dashscope_key"]:
        missing.append("DASHSCOPE_API_KEY（阿里云百炼，粤语识别）")
    if args.provider == "doubao" and not cfg["ark_key"]:
        missing.append("ARK_API_KEY（火山方舟豆包，翻译）")
    if args.provider == "openai" and not cfg["openai_key"]:
        missing.append("OPENAI_API_KEY（翻译）")
    if args.provider == "custom" and not (args.base_url or cfg["custom_base_url"]):
        missing.append("--base-url 或 CUSTOM_BASE_URL（自定义翻译接口地址）")
    if missing:
        sys.exit("错误：缺少密钥 " + "、".join(missing) + "。请在 .env 或环境变量中配置。")

    try:
        outputs = pipeline.run(
            input_path=args.input,
            output_dir=args.output,
            provider=args.provider,
            mandarin_only=args.mandarin_only,
            no_burn=args.no_burn,
            font=args.font,
            font_size=args.font_size,
            model=args.model,
            keep_temp=args.keep_temp,
            asr_engine=args.asr_engine,
            model_dir=args.model_dir,
            model_size=args.model_size,
            dashscope_key=cfg["dashscope_key"],
            ark_key=cfg["ark_key"],
            openai_key=cfg["openai_key"],
            custom_base_url=args.base_url or cfg["custom_base_url"],
            custom_key=args.custom_key or cfg["custom_key"],
            log=print,
        )
    except Exception as e:  # noqa: BLE001
        sys.exit(f"处理失败：{e}")

    print("\n===== 输出清单 =====")
    for f in outputs:
        print(" ", Path(f).name)


if __name__ == "__main__":
    main()
