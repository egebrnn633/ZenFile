import shutil
import time
from pathlib import Path
from watchdog.events import FileSystemEventHandler


class FileOrganizer(FileSystemEventHandler):
    # ✅ 关键修正：这里必须接收 config 和 logger 两个参数
    def __init__(self, config, logger):
        self.watch_dir = Path(config["watch_dir"])
        self.rules = config["rules"]
        self.ignore_exts = config["ignore_exts"]
        self.logger = logger  # 保存 logger 以便后续使用

    def on_modified(self, event):
        if not event.is_directory: self.process_file(event.src_path)

    def on_moved(self, event):
        if not event.is_directory: self.process_file(event.dest_path)

    def on_created(self, event):
        if not event.is_directory: self.process_file(event.src_path)

    def process_file(self, file_path_str):
        file_path = Path(file_path_str)

        # 1. 安全检查
        if not file_path.exists() or file_path.name.startswith("."):
            return
        if file_path.suffix.lower() in self.ignore_exts:
            return

        # 2. 匹配规则
        target_folder_name = "99_其他"
        ext = file_path.suffix.lower()

        for folder, ext_list in self.rules.items():
            if ext in ext_list:
                target_folder_name = folder
                break

        self.move_file(file_path, target_folder_name)

    def move_file(self, file_path, folder_name):
        target_dir = self.watch_dir / folder_name

        try:
            target_dir.mkdir(exist_ok=True)
            target_path = target_dir / file_path.name

            # 3. 自动重命名处理
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
                counter += 1

            # 稍作等待，防止文件占用
            time.sleep(0.5)

            shutil.move(str(file_path), str(target_path))

            # ✅ 使用 logger 记录日志
            self.logger.info(f"成功整理: {file_path.name} -> {folder_name}")

        except Exception as e:
            # ✅ 记录错误日志
            self.logger.error(f"移动失败 {file_path.name}: {str(e)}")