import tkinter as tk
import customtkinter as ctk


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)

    def show(self, e=None):
        if self.tip: return

        # 计算位置
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        self.tip.attributes("-topmost", True)

        # 根据当前主题决定背景色
        mode = ctk.get_appearance_mode()
        bg_color = "#2b2b2b" if mode == "Dark" else "#f0f0f0"
        text_color = "#ffffff" if mode == "Dark" else "#000000"
        border_color = "#565b5e" if mode == "Dark" else "#cccccc"

        # 外层 Frame 实现边框
        frame = ctk.CTkFrame(
            self.tip,
            corner_radius=6,
            fg_color=bg_color,
            border_width=1,
            border_color=border_color
        )
        frame.pack(fill="both", expand=True)

        # 文本标签
        label = ctk.CTkLabel(
            frame,
            text=self.text,
            text_color=text_color,
            font=("Microsoft YaHei UI", 12),
            padx=10,
            pady=5
        )
        label.pack()

    def hide(self, e=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


def center_window(root, w=500, h=550):
    root.update_idletasks()
    # 获取屏幕尺寸
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    # 计算位置
    x = (ws // 2) - (w // 2)
    y = (hs // 2) - (h // 2)
    root.geometry(f'{w}x{h}+{x}+{y}')


class HotkeyRecorder(ctk.CTkEntry):
    def __init__(self, parent, default_value="", **kwargs):
        super().__init__(parent, **kwargs)
        self.default = default_value

        # 初始化显示
        self.insert(0, default_value)
        # CTK Entry 没有 'readonly' 状态用于完全禁止输入但允许代码修改
        # 我们通过事件拦截来控制输入，所以这里保持 normal
        self.configure(state='normal')

        self.keys = set()

        # 绑定事件
        self.bind('<FocusIn>', self.on_focus)
        self.bind('<FocusOut>', self.on_blur)
        self.bind('<KeyPress>', self.on_key)

        # 记录原始颜色以便恢复
        self._default_border = self._border_color

    def on_focus(self, e):
        """获得焦点时：清空并提示录制，边框变绿"""
        self.delete(0, tk.END)
        self.insert(0, "请按下组合键...")
        self.keys.clear()

        # 视觉反馈：边框变为主题色(绿色)，文字变亮
        self.configure(border_color="#2CC985")

    def on_blur(self, e):
        """失去焦点时：如果没有录制有效键，恢复默认值"""
        current_text = self.get()
        if "按下" in current_text or not current_text.strip():
            self.delete(0, tk.END)
            self.insert(0, self.default)

        # 恢复视觉样式
        self.configure(border_color=self._default_border)

    def on_key(self, e):
        """处理按键事件"""
        k = e.keysym.lower()

        # 忽略单独的修饰键按下（只在组合时记录）或无效键
        if k in ["control_l", "control_r", "alt_l", "alt_r", "shift_l", "shift_r", "caps_lock", "win"]:
            return "break"

        mapping = {
            "control_l": "<ctrl>", "control_r": "<ctrl>",
            "alt_l": "<alt>", "alt_r": "<alt>",
            "shift_l": "<shift>", "shift_r": "<shift>",
            "return": "enter"
        }

        # 构建当前按下的修饰键
        mods = []
        if e.state & 0x0004: mods.append("<ctrl>")
        if e.state & 0x20000 or e.state & 0x0008: mods.append("<alt>")  # Alt check varies by OS
        if e.state & 0x0001: mods.append("<shift>")

        # 获取主键名
        key_name = mapping.get(k, k)

        # 组合去重
        current_combo = set(mods)
        current_combo.add(key_name)

        # 排序：Ctrl -> Alt -> Shift -> Key
        s = sorted(list(current_combo),
                   key=lambda x: 0 if "ctrl" in x else 1 if "alt" in x else 2 if "shift" in x else 3)

        final_str = "+".join(s)

        self.delete(0, tk.END)
        self.insert(0, final_str)

        return "break"  # 阻止默认的字符输入

    def get_hotkey(self):
        v = self.get()
        return self.default if "按下" in v else v