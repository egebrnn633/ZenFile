import sys, os, platform, threading
import tkinter as tk
import customtkinter as ctk  # 引入 CTK
import pystray
from PIL import Image
from pystray import MenuItem as item

from zenfile.utils.system import get_resource_path
from pynput import keyboard
from zenfile.utils.config import load_config
from zenfile.utils.logger import setup_logger
from zenfile.core.organizer import Organizer
from zenfile.core.monitor import MonitorManager

if platform.system() == "Windows":
    import win32event, win32api, winerror

# 设置 CTK 全局主题 (建议放在文件最上方)
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class HotkeyManager:
    def __init__(self, logger, cb):
        self.logger = logger
        self.cb = cb
        self.listener = None

    def start(self, key):
        self.stop()
        if not key: return
        try:
            self.listener = keyboard.GlobalHotKeys({key: lambda: self.cb()})
            self.listener.start()
            self.logger.info(f"快捷键注册: {key}")
        except Exception as e:
            self.logger.error(f"快捷键失败: {e}")

    def stop(self):
        if self.listener:
            try:
                self.listener.stop()
            except:
                pass
            self.listener = None

    def restart(self, key):
        self.start(key)


class SystemTray:
    def __init__(self, root, organizer, monitor_mgr, hotkey_mgr, on_quit):
        self.root = root  # 这里传入的是 ctk.CTk 实例
        self.organizer = organizer
        self.monitor_mgr = monitor_mgr
        self.hotkey_mgr = hotkey_mgr
        self.on_quit = on_quit
        self.icon = None
        self.win = None

        # 预加载图标
        try:
            self.imgs = {
                "run": Image.open(get_resource_path("assets/icons/logo.png")),
                "pause": Image.open(get_resource_path("assets/icons/pause.png"))
            }
        except Exception as e:
            print(f"图标加载失败: {e}")
            self.imgs = {
                "run": Image.new('RGB', (64, 64), color='blue'),
                "pause": Image.new('RGB', (64, 64), color='gray')
            }

    def run(self):
        self.icon = pystray.Icon("ZenFile", self.imgs["run"], "ZenFile (运行中)", self.menu())
        self.icon.run()

    def stop_service(self):
        """显式停止服务，消除幽灵图标"""
        if self.icon:
            self.icon.visible = False
            self.icon.stop()

    def menu(self):
        return pystray.Menu(
            item('设置', self.open_settings),
            item('暂停/恢复', self.toggle, checked=lambda i: self.organizer.paused),
            item('退出', self.quit)
        )

    def toggle(self, i=None, it=None):
        paused = not self.organizer.paused
        self.organizer.set_paused(paused)
        if self.icon:
            state = "pause" if paused else "run"
            self.icon.icon = self.imgs[state]
            self.icon.title = f"ZenFile ({'已暂停' if paused else '运行中'})"
            try:
                self.icon.notify(f"整理已{'暂停' if paused else '恢复'}", "状态变更")
            except:
                pass
            self.icon.update_menu()

    def open_settings(self, i, it):
        # 必须抛回主线程执行 GUI 操作
        self.root.after(0, self._show_win)

    def _show_win(self):
        if self.win and self.win.winfo_exists():
            self.win.lift()
            self.win.focus_force()
            return

        try:
            # 注意这里路径可能需要调整，取决于你的文件结构
            # 假设 main_window.py 和 main.py 在同级目录: from .main_window import SettingsWindow
            from .main_window import SettingsWindow

            # 使用 CTkToplevel 创建现代化窗口
            self.win = ctk.CTkToplevel(self.root)
            # 必须设置属性防止被垃圾回收或意外关闭
            self.win.protocol("WM_DELETE_WINDOW", self._on_win_close)

            SettingsWindow(self.win, self.organizer, self.monitor_mgr, self.hotkey_mgr)

            # 确保窗口显示在最前
            self.win.lift()
            self.win.focus_force()
        except Exception as e:
            print(f"打开设置窗口失败: {e}")
            import traceback
            traceback.print_exc()

    def _on_win_close(self):
        if self.win:
            self.win.destroy()
            self.win = None

    def quit(self, i, it):
        if self.on_quit: self.on_quit()


def main():
    # 1. 单例 (Windows)
    if platform.system() == "Windows":
        mutex = win32event.CreateMutex(None, False, "Global\\ZenFile_v1_Lock")
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            sys.exit(0)

    # 2. 基础配置
    logger = setup_logger()
    config = load_config()
    logger.info(">>> ZenFile 启动")

    # 3. 核心对象初始化
    # 使用 CTk 替代 Tk 作为根窗口
    root = ctk.CTk()
    root.withdraw()  # 隐藏主窗口，只显示托盘

    # 必须在主循环开始前配置好 DPI 感知（CTK 会自动处理，但为了稳妥）
    if platform.system() == "Windows":
        try:
            ctk.deactivate_automatic_dpi_awareness()  # 如果布局错乱可尝试开启或关闭此行
        except:
            pass

    org = Organizer(config, logger)
    mon_mgr = MonitorManager(org, logger)
    mon_mgr.start(config.get("watch_dirs", []))

    # 4. 退出逻辑
    def shutdown():
        logger.info("退出中...")
        hk_mgr.stop()
        tray.stop_service()
        mon_mgr.stop()
        try:
            root.quit()
        except:
            pass
        os._exit(0)

    # 5. 组装
    hk_mgr = HotkeyManager(logger, lambda: tray.toggle())
    tray = SystemTray(root, org, mon_mgr, hk_mgr, shutdown)

    # 6. 启动
    hk_mgr.start(config.get("hotkey", "<ctrl>+<alt>+z"))

    # 托盘图标必须在独立线程运行，否则会阻塞 GUI 主循环
    threading.Thread(target=tray.run, daemon=True).start()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()