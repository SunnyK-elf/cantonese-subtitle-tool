"""配置加载：从 .env 文件或环境变量读取 API Key。"""
import os
from pathlib import Path

try:  # python-dotenv 可选，未安装时直接读环境变量
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


def load_config():
    """读取配置，返回 dict。优先环境变量，其次 .env 文件。"""
    # 尝试从当前目录及项目根目录加载 .env
    if load_dotenv is not None:
        load_dotenv(Path(".env"))
    return {
        "dashscope_key": os.getenv("DASHSCOPE_API_KEY", "").strip(),
        "ark_key": os.getenv("ARK_API_KEY", "").strip(),
        "openai_key": os.getenv("OPENAI_API_KEY", "").strip(),
        "custom_base_url": os.getenv("CUSTOM_BASE_URL", "").strip(),
        "custom_key": os.getenv("CUSTOM_API_KEY", "").strip(),
    }
