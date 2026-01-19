import shutil
import time
import sys
import uuid
import threading
from pathlib import Path
from .history import HistoryManager
from .rules import RuleMatcher


class Organizer:
    def __init__(self, config, logger):
        self.logger = logger
        self.paused = False
        self.ignore_next_paths = set()
        self.ignore_lock = threading.Lock()
        self.reload_config(config)

    def reload_config(self, new_config):
        self.config = new_config
        self.matcher = RuleMatcher(new_config)
        raw_dirs = new_config.get("watch_dirs", [])
        self.watch_dirs = []
        for p in raw_dirs:
            try:
                path_obj = Path(p)
                if path_obj.exists():
                    self.watch_dirs.append(path_obj)
            except:
                pass
        self.logger.info(f"配置重载完成，当前生效目录数: {len(self.watch_dirs)}")

    def set_paused(self, paused):
        self.paused = paused
        state = "暂停" if paused else "恢复"
        self.logger.info(f"监控已{state}")

    def process_file(self, file_path_str, force=False, batch_id=None):
        if self.paused and not force: return
        try:
            file_path = Path(file_path_str)
            # 白名单检查
            path_key = str(file_path).lower() if sys.platform == 'win32' else str(file_path)
            with self.ignore_lock:
                if path_key in self.ignore_next_paths:
                    self.ignore_next_paths.remove(path_key)
                    return

            if not file_path.exists(): return
            if getattr(sys, 'frozen', False) and file_path == Path(sys.executable): return
            if file_path.name.startswith(".") or file_path.name.startswith("~$"): return

            should_ignore, target_folder = self.matcher.match(file_path)
            if should_ignore: return

            self._move_file(file_path, target_folder, batch_id)
        except Exception as e:
            self.logger.error(f"处理出错 {file_path_str}: {e}")

    def _move_file(self, source, folder, batch_id=None):
        target_dir = source.parent / folder
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / source.name
            counter = 1
            while target.exists():
                target = target_dir / f"{source.stem}_{counter}{source.suffix}"
                counter += 1

            time.sleep(0.05)
            shutil.move(str(source), str(target))
            HistoryManager.add_record(source, target, batch_id)
            self.logger.info(f"整理: {source.name} -> {folder}")
            return True
        except Exception as e:
            self.logger.error(f"移动失败 {source.name}: {e}")
            return False

    def run_now(self):
        self.logger.info(">>> 开始一键整理")
        count = 0
        batch_id = str(uuid.uuid4())
        current_dirs = list(self.watch_dirs)
        for d in current_dirs:
            if not d.exists(): continue
            try:
                for f in d.iterdir():
                    if f.is_file():
                        self.process_file(f, force=True, batch_id=batch_id)
                        count += 1
            except Exception as e:
                self.logger.error(f"扫描失败 {d}: {e}")
        self.logger.info(f"<<< 整理完成，处理 {count} 个文件")
        return count

    def undo_last_action(self):
        records = HistoryManager.pop_last_batch()
        if not records: return False, "无可撤销操作"
        success, fail = 0, 0
        for rec in records:
            try:
                src = Path(rec['source'])
                tgt = Path(rec['target'])
                if not tgt.exists():
                    fail += 1;
                    continue

                if src.exists():
                    src = src.parent / f"{src.stem}_undo{src.suffix}"

                src.parent.mkdir(parents=True, exist_ok=True)

                # 加入白名单
                key = str(src).lower() if sys.platform == 'win32' else str(src)
                with self.ignore_lock:
                    self.ignore_next_paths.add(key)

                shutil.move(str(tgt), str(src))
                success += 1
            except:
                fail += 1
        return True, f"成功撤销 {success} 个，失败 {fail} 个"