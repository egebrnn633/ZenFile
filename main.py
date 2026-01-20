import sys
import os
import platform
import threading
import tkinter as tk
from pathlib import Path
from pynput import keyboard

# 引入核心组件
from zenfile.utils.config import load_config
from zenfile.utils.logger import setup_logger
from zenfile.core.organizer import Organizer
from zenfile.core.monitor import MonitorManager
from zenfile.ui.tray import SystemTray

# Windows 单例锁
if platform.system() == "Windows":
    import win32event, win32api, winerror

def check_single_instance():
    if platform.system() == "Windows":
        mutex = win32event.CreateMutex(None, False, "Global\\ZenFile_v1_Lock")
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            return False, mutex
        return True, mutex
    return True, None

class HotkeyManager:
    """热键管理器：支持动态重载"""
    def __init__(self, logger, callback):
        self.logger = logger
        self.callback = callback
        self.listener = None
        self.current_hotkey = None

    def start(self, hotkey_str):
        self.stop() # 先停止旧的
        if not hotkey_str:
            return

        self.current_hotkey = hotkey_str
        try:
            # 封装回调，确保异常不崩溃
            def on_activate():
                try:
                    self.callback()
                except Exception as e:
                    self.logger.error(f"快捷键回调出错: {e}")

            hotkey_map = {hotkey_str: on_activate}
            self.listener = keyboard.GlobalHotKeys(hotkey_map)
            self.listener.start()
            self.logger.info(f"快捷键已注册: {hotkey_str}")
        except Exception as e:
            self.logger.error(f"快捷键注册失败 [{hotkey_str}]: {e}")

    def stop(self):
        if self.listener:
            try:
                self.listener.stop()
                self.logger.info("旧快捷键监听已停止")
            except:
                pass
            self.listener = None

    def restart(self, new_hotkey):
        self.logger.info(f"正在更新快捷键为: {new_hotkey}")
        self.start(new_hotkey)


def main():
    # 单例检查
    is_unique, mutex = check_single_instance()
    if not is_unique:
        sys.exit(0)

    # 初始化
    logger = setup_logger()
    config = load_config()
    logger.info(">>> ZenFile 启动中...")

    #  GUI 上下文
    root = tk.Tk()
    root.withdraw()

    #业务逻辑
    organizer = Organizer(config, logger)
    monitor_manager = MonitorManager(organizer, logger)
    monitor_manager.start(config.get("watch_dirs", []))

    # 定义退出逻辑
    def app_shutdown():
        logger.info("正在退出应用程序...")
        if hotkey_manager: hotkey_manager.stop()
        if tray and tray.icon: tray.icon.stop()
        monitor_manager.stop()
        try: root.quit()
        except: pass
        os._exit(0)

    # 初始化热键管理器 (先定义，稍后传递给 Tray)
    # 这里我们定义一个临时的 callback proxy，因为 tray 还没初始化
    def hotkey_callback():
        if tray: tray.toggle()

    hotkey_manager = HotkeyManager(logger, hotkey_callback)

    #初始化托盘
    tray = SystemTray(root, organizer, monitor_manager, hotkey_manager, on_quit=app_shutdown)

    # 启动热键
    initial_hotkey = config.get("hotkey", "<ctrl>+<alt>+z")
    hotkey_manager.start(initial_hotkey)

    # 启动托盘线程
    tray_thread = threading.Thread(target=tray.run, daemon=True)
    tray_thread.start()

    # 主循环
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app_shutdown()

if __name__ == "__main__":
    main()