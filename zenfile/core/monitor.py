import time
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

class FileMonitor(FileSystemEventHandler):
    def __init__(self, organizer):
        self.organizer = organizer
    def on_created(self, event):
        if not event.is_directory: self.organizer.process_file(event.src_path)
    def on_modified(self, event):
        if not event.is_directory: self.organizer.process_file(event.src_path)
    def on_moved(self, event):
        if not event.is_directory: self.organizer.process_file(event.dest_path)

class MonitorManager:
    def __init__(self, organizer, logger):
        self.organizer = organizer
        self.logger = logger
        self.observer = Observer()
        self.handler = FileMonitor(organizer)
        self.running = False

        self.health_check_running = False
        # 活跃列表
        self.active_watch_paths = set()
        # 配置列表
        self.config_watch_paths = set()

    def start(self, dirs):
        self.config_watch_paths = set(str(Path(p)) for p in dirs)

        self.update_watches(dirs)
        if not self.running:
            self.observer.start()
            self.running = True
            self.logger.info("监控服务启动")

        if not self.health_check_running:
            self.health_check_running = True
            threading.Thread(target=self._health_check_loop, daemon=True).start()
            self.logger.info("目录健康检查服务已启动")

    def stop(self):
        self.health_check_running = False

        if self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False

    def update_watches(self, new_dirs):
        self.config_watch_paths = set(str(Path(p)) for p in new_dirs)

        self.observer.unschedule_all()

        self.active_watch_paths.clear()
        count = 0
        for p in new_dirs:
            path = Path(p)
            if path.exists():
                try:
                    self.observer.schedule(self.handler, str(path), recursive=False)
                    self.active_watch_paths.add(str(path))
                    count += 1
                except: pass
        self.logger.info(f"监控列表更新，共监控 {count} 个目录")

    # 心跳检测
    def _health_check_loop(self):
        while self.health_check_running:
            time.sleep(3)  # 每3秒检查一次
            try:
                reload = False

                # 检查目录是否丢失
                for p in list(self.active_watch_paths):
                    if not Path(p).exists():
                        self.logger.warning(f"目录丢失: {p}")
                        reload = True

                # 检查目录是否恢复 (在配置里但不在活跃列表里)
                missing = self.config_watch_paths - self.active_watch_paths
                for p in missing:
                    if Path(p).exists():
                        self.logger.info(f"目录恢复: {p}")
                        reload = True

                if reload:
                    self.update_watches(list(self.config_watch_paths))
            except Exception as e:
                self.logger.error(f"健康检查错: {e}")
