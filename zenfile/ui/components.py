import tkinter as tk

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)
    def show(self, e=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        self.tip.attributes("-topmost", True)
        tk.Label(self.tip, text=self.text, bg="#ffffe0", relief="solid", bd=1).pack()
    def hide(self, e=None):
        if self.tip: self.tip.destroy(); self.tip = None

def center_window(root, w=500, h=550):
    root.update_idletasks()
    ws, hs = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f'{w}x{h}+{(ws//2)-(w//2)}+{(hs//2)-(h//2)}')

class HotkeyRecorder(tk.Entry):
    def __init__(self, parent, default_value="", **kwargs):
        super().__init__(parent, **kwargs)
        self.default = default_value
        self.insert(0, default_value)
        self.config(state='readonly')
        self.keys = set()
        self.bind('<FocusIn>', self.on_focus)
        self.bind('<FocusOut>', self.on_blur)
        self.bind('<KeyPress>', self.on_key)
    def on_focus(self, e):
        self.config(state='normal', bg='#e0f7fa')
        self.delete(0, tk.END); self.insert(0, "按下快捷键...")
        self.config(state='readonly'); self.keys.clear()
    def on_blur(self, e):
        self.config(state='normal', bg='white')
        if "按下" in self.get() or not self.get().strip():
            self.delete(0, tk.END); self.insert(0, self.default)
        self.config(state='readonly')
    def on_key(self, e):
        k = e.keysym.lower()
        mapping = {"control_l":"<ctrl>", "control_r":"<ctrl>", "alt_l":"<alt>", "alt_r":"<alt>", "shift_l":"<shift>", "shift_r":"<shift>"}
        self.keys.add(mapping.get(k, k))
        s = sorted(list(self.keys), key=lambda x: 0 if "ctrl" in x else 1 if "alt" in x else 2)
        self.config(state='normal'); self.delete(0, tk.END); self.insert(0, "+".join(s)); self.config(state='readonly')
        return "break"
    def get_hotkey(self):
        v = self.get()
        return self.default if "按下" in v else v