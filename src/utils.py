import json
import os
import sys
import logging
from pathlib import Path


# 获取运行目录
def get_base_dir():
    app_data = os.getenv('APPDATA')
    zenfile_dir = Path(app_data) / "ZenFile"
    zenfile_dir.mkdir(parents=True, exist_ok=True)
    return zenfile_dir

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

BASE_DIR = get_base_dir()
CONFIG_PATH = BASE_DIR / "config" / "settings.json"
LOG_DIR = BASE_DIR / "logs"

#--- 下载临时文件 ---
# ".tmp",
# ".crdownload",  # Chrome/Edge
# ".download",  # Safari
# ".part",  # Firefox
# ".opdownload",  # Opera
#
#--- 快捷方式 ---
# ".lnk",  # 软件快捷方式
# ".url",  # 网页快捷方式
#
# --- 系统与配置 ---
# ".ini",  # desktop.ini
# ".db",  # Thumbs.db
# ".sys",  # 系统文件
#
#--- 备份与日志 ---
# ".bak",
# ".log",
# ".old"


def load_config():
    """读取配置"""
    if not CONFIG_PATH.exists():
        # 默认配置
        return {
            "watch_dirs": [],
            "hotkey": "<ctrl>+<alt>+z",
            "rules": {
                "01_图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
                "02_文档": [".pdf", ".docx", ".doc", ".txt", ".md", ".xlsx", ".xls", ".pptx", ".ppt", ".csv"],
                "03_视频": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"],
                "04_音频": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"],
                "05_压缩包": [".zip", ".rar", ".7z", ".tar", ".gz", ".iso"],
                "06_安装包": [".exe", ".msi"],
                "07_代码": [".py", ".java", ".html", ".css", ".js", ".json", ".sql", ".c", ".cpp"]
            },
            "ignore_exts": [".tmp", ".crdownload", ".download", ".part", ".opdownload", ".lnk", ".url", ".ini", ".db",
                            ".sys", ".bak", ".log", ".old", ".sav", ".lock"]
        }

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    """保存配置到文件"""
    # 确保 config 目录存在
    CONFIG_PATH.parent.mkdir(exist_ok=True)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def setup_logger():
    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger("ZenFile")
    logger.setLevel(logging.INFO)
    if logger.handlers: return logger
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    file_handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger