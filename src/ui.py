import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pynput.keyboard import HotKey

from src.utils import load_config, save_config
from src.startup import set_autorun, is_autorun_enabled


class SettingsWindow:
    def __init__(self, root, on_save_callback):
        self.root = root
        self.root.title("ZenFile 设置")
        self.root.geometry("500x420")  # 稍微加高一点

        # 1. 强制置顶 (解决被遮挡问题)
        self.root.attributes('-topmost', True)

        # 2. 窗口居中 (解决出现在右上角问题)
        self.center_window()

        self.on_save_callback = on_save_callback
        self.config = load_config()

        # === 布局 ===
        notebook = ttk.Notebook(root)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Tab 1: 监控目录
        self.frame_dirs = ttk.Frame(notebook)
        notebook.add(self.frame_dirs, text='监控目录')
        self.setup_dirs_tab()

        # Tab 2: 常规设置
        self.frame_general = ttk.Frame(notebook)
        notebook.add(self.frame_general, text='常规设置')
        self.setup_general_tab()

        # 底部按钮
        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(btn_frame, text="保存并生效", command=self.save_settings).pack(side='right')

        # 强制聚焦
        self.root.focus_force()

    def center_window(self):
        """精确计算并居中窗口"""
        self.root.update_idletasks()  # 关键：先刷新一下计算尺寸
        width = 500
        height = 420
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_dirs_tab(self):
        self.list_box = tk.Listbox(self.frame_dirs, selectmode=tk.SINGLE)
        self.list_box.pack(expand=True, fill='both', padx=5, pady=5)

        for path in self.config.get("watch_dirs", []):
            self.list_box.insert(tk.END, path)

        btn_bar = ttk.Frame(self.frame_dirs)
        btn_bar.pack(fill='x', padx=5, pady=5)
        ttk.Button(btn_bar, text="➕ 添加目录", command=self.add_dir).pack(side='left', padx=2)
        ttk.Button(btn_bar, text="➖ 删除选中", command=self.remove_dir).pack(side='left', padx=2)

    def setup_general_tab(self):
        # 1. 开机自启
        self.var_autorun = tk.BooleanVar(value=is_autorun_enabled())
        chk_autorun = ttk.Checkbutton(self.frame_general, text="开机自动启动 ZenFile", variable=self.var_autorun)
        chk_autorun.pack(anchor='w', padx=20, pady=20)

        # 2. 快捷键设置 (智能录制)
        lbl_frame = ttk.LabelFrame(self.frame_general, text="全局快捷键 (点击下方录制)")
        lbl_frame.pack(fill='x', padx=20, pady=10)

        self.entry_hotkey = ttk.Entry(lbl_frame)
        self.entry_hotkey.pack(fill='x', padx=10, pady=10)

        current_hotkey = self.config.get("hotkey", "<ctrl>+<alt>+z")
        self.entry_hotkey.insert(0, current_hotkey)

        # 绑定键盘事件，实现智能录制
        self.entry_hotkey.bind("<KeyPress>", self.on_hotkey_press)
        # 防止用户手动删除导致格式错误，设为只读 (通过代码修改)
        # self.entry_hotkey.config(state='readonly') # 可选：如果觉得太严格可以注释掉

        ttk.Label(lbl_frame, text="提示：请直接在输入框内按下键盘组合键\n例如同时按下 Ctrl 和 F1").pack(anchor='w', padx=10, pady=5)

    def on_hotkey_press(self, event):
        """智能识别键盘按键，自动格式化为 pynput 格式"""
        keys = []

        # 识别修饰键 (Ctrl, Alt, Shift)
        # event.state 是一个位掩码，不同系统可能略有不同，这里是通用判断
        if event.state & 0x0004 or "Control" in event.keysym:
            keys.append("<ctrl>")
        if event.state & 0x0001 or "Shift" in event.keysym:
            keys.append("<shift>")
        if event.state & 0x20000 or event.state & 0x0008 or "Alt" in event.keysym:
            keys.append("<alt>")

        # 识别主键 (过滤掉单纯的修饰键按下)
        key = event.keysym.lower()
        if key not in ["control_l", "control_r", "alt_l", "alt_r", "shift_l", "shift_r"]:
            # 处理特殊键名映射
            if key == "return":
                key = "<enter>"
            elif key == "space":
                key = "<space>"
            elif key.startswith("f") and key[1:].isdigit():
                key = f"<{key}>"  # F1-F12
            else:
                keys.append(key)

        # 如果只有修饰键，暂时不更新
        if not keys: return "break"

        # 只有当按下了非修饰键，或者组合键时才更新
        hotkey_str = "+".join(keys)

        # 更新输入框
        self.entry_hotkey.delete(0, tk.END)
        self.entry_hotkey.insert(0, hotkey_str)

        # 阻止默认输入行为
        return "break"

    def add_dir(self):
        # 指定 parent，防止弹窗跑到后面
        path = filedialog.askdirectory(parent=self.root)
        if path:
            current_paths = self.list_box.get(0, tk.END)
            if path not in current_paths:
                self.list_box.insert(tk.END, path)
            self.root.lift()
            self.root.focus_force()

    def remove_dir(self):
        selection = self.list_box.curselection()
        if selection:
            self.list_box.delete(selection[0])

    def save_settings(self):
        new_dirs = list(self.list_box.get(0, tk.END))
        self.config["watch_dirs"] = new_dirs

        new_hotkey = self.entry_hotkey.get().strip()
        if not new_hotkey:
            # 3. 指定 parent=self.root，解决弹窗被遮挡
            messagebox.showwarning("提示", "快捷键不能为空", parent=self.root)
            return

        try:
            HotKey.parse(new_hotkey)
        except Exception:
            messagebox.showerror("格式错误",
                                 "快捷键无法识别！请点击输入框并直接按下键盘组合键。",
                                 parent=self.root)
            return

        self.config["hotkey"] = new_hotkey

        try:
            save_config(self.config)
            set_autorun(self.var_autorun.get())

            if self.on_save_callback:
                self.on_save_callback(self.config)

            messagebox.showinfo("成功", "设置已保存！", parent=self.root)
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}", parent=self.root)