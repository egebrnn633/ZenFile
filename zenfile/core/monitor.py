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

    def start(self, dirs):
        self.update_watches(dirs)
        if not self.running:
            self.observer.start()
            self.running = True
            self.logger.info("监控服务启动")

    def stop(self):
        if self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False

    def update_watches(self, new_dirs):
        self.observer.unschedule_all()
        count = 0
        for p in new_dirs:
            path = Path(p)
            if path.exists():
                try:
                    self.observer.schedule(self.handler, str(path), recursive=False)
                    count += 1
                except: pass
        self.logger.info(f"监控列表更新，共监控 {count} 个目录")