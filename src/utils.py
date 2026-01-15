import json
import os
import logging
from pathlib import Path

# 获取项目根目录 (即 main.py 所在的目录)
# __file__ 是当前文件路径，parent 是 src，parent.parent 是 ZenFile 根目录
BASE_DIR = Path(__file__).parent.parent


def load_config():
    """读取 config/settings.json 配置文件"""
    config_path = BASE_DIR / "config" / "settings.json"

    # 检查文件是否存在
    if not config_path.exists():
        # 如果找不到，抛出异常，提示用户
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 处理路径中的 ~ (代表用户目录，例如 C:\Users\YourName)
    if config["watch_dir"].startswith("~"):
        config["watch_dir"] = os.path.expanduser(config["watch_dir"])

    return config


def setup_logger():
    """配置日志系统"""
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)  # 如果 logs 文件夹不存在，自动创建

    logger = logging.getLogger("ZenFile")
    logger.setLevel(logging.INFO)

    # 防止日志重复打印 (避免出现两条一样的日志)
    if logger.handlers:
        return logger

    # 1. 设置日志格式
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')

    # 2. 输出到文件 (logs/app.log)
    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    # 3. 输出到控制台 (IDEA 下方的黑框框)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger