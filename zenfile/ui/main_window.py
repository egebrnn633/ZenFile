import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from zenfile.utils.config import save_config
from zenfile.utils.system import set_autorun, is_autorun_enabled
from .components import center_window, HotkeyRecorder, ToolTip


class SettingsWindow:
    def __init__(self, window, organizer, monitor_mgr, hotkey_mgr):
        self.window = window
        self.organizer = organizer
        self.monitor_mgr = monitor_mgr
        self.hotkey_mgr = hotkey_mgr
        self.config = organizer.config

        self.window.title("ZenFile 设置")
        center_window(self.window)
        self.window.resizable(False, False)

        nb = ttk.Notebook(self.window)
        nb.pack(fill='both', expand=True, padx=10, pady=10)
        f1, f2 = ttk.Frame(nb), ttk.Frame(nb)
        nb.add(f1, text='常规');
        nb.add(f2, text='目录')

        # 常规
        self.v_run = tk.BooleanVar(value=is_autorun_enabled())
        ttk.Checkbutton(f1, text="开机自启", variable=self.v_run, command=self.tog_run).pack(anchor='w', padx=20, pady=20)

        gf = ttk.LabelFrame(f1, text="快捷键")
        gf.pack(fill='x', padx=20)
        self.hk = HotkeyRecorder(gf, default_value=self.config.get("hotkey", "<ctrl>+<alt>+z"))
        self.hk.pack(fill='x', padx=10, pady=10)

        af = ttk.LabelFrame(f1, text="操作")
        af.pack(fill='x', padx=20, pady=10)
        ttk.Button(af, text="立即整理", command=self.run_now).pack(side='left', padx=10, pady=10)
        ttk.Button(af, text="撤销一步", command=self.undo).pack(side='left', padx=10, pady=10)

        # 目录
        self.lb = tk.Listbox(f2, height=15)
        self.lb.pack(fill='both', padx=10, pady=10)
        for p in self.config.get("watch_dirs", []): self.lb.insert(tk.END, p)
        bf = ttk.Frame(f2)
        bf.pack(fill='x', padx=10)
        ttk.Button(bf, text="添加", command=self.add).pack(side='left');
        ttk.Button(bf, text="删除", command=self.rem).pack(side='left')

        ttk.Button(self.window, text="保存", command=self.save).pack(pady=10)

    def run_now(self):
        c = self.organizer.run_now()
        messagebox.showinfo("完成", f"已处理 {c} 个文件")

    def undo(self):
        s, m = self.organizer.undo_last_action()
        messagebox.showinfo("结果", m)

    def tog_run(self):
        if not set_autorun(self.v_run.get()): self.v_run.set(not self.v_run.get())

    def add(self):
        p = filedialog.askdirectory()
        if p and p not in self.lb.get(0, tk.END): self.lb.insert(tk.END, p)

    def rem(self):
        s = self.lb.curselection()
        if s: self.lb.delete(s)

    def save(self):
        dirs = list(self.lb.get(0, tk.END))
        hk = self.hk.get_hotkey()
        self.config.update({"watch_dirs": dirs, "hotkey": hk})
        save_config(self.config)

        self.organizer.reload_config(self.config)
        self.monitor_mgr.update_watches(dirs)
        self.hotkey_mgr.restart(hk)

        messagebox.showinfo("成功", "配置已保存并立即生效")
        self.window.destroy()