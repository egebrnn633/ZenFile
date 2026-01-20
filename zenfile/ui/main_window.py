from tkinter import messagebox, filedialog, ttk
from PIL import Image
import tkinter as tk
import customtkinter as ctk
from zenfile.utils.config import save_config
from zenfile.utils.system import set_autorun, is_autorun_enabled
from zenfile.core.history import HistoryManager
from .components import center_window, HotkeyRecorder

# --- 样式常量定义 ---
COLOR_BG = "#F5F7FA"  # 整体背景灰
COLOR_WHITE = "#FFFFFF"  # 卡片背景白
COLOR_TEXT_MAIN = "#333333"  # 主要文字
COLOR_TEXT_SUB = "#666666"  # 次要文字
COLOR_GREEN = "#2CC985"  # 运行中/保存
COLOR_BLUE = "#3B8EDF"  # 立即整理
COLOR_ORANGE = "#F29F3F"  # 撤销
COLOR_RED = "#FF4D4F"  # 删除
COLOR_BORDER = "#E1E4E8"  # 边框颜色

# 设置全局主题配置
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class SettingsWindow:
    def __init__(self, window, organizer, monitor_mgr, hotkey_mgr):
        # 1. 基础窗口设置
        self.window = window
        self.organizer = organizer
        self.monitor_mgr = monitor_mgr
        self.hotkey_mgr = hotkey_mgr
        self.config = organizer.config

        self.window.title("设置")
        try:
            # 请确保 assets 文件夹里有 logo.ico
            self.window.iconbitmap("assets/icons/applogo.ico")
        except Exception as e:
            print(f"窗口图标加载失败: {e}")
        center_window(self.window, 1200, 700)

        # 2. 数据状态初始化
        self.current_page = None
        self.pages = {}
        self.nav_buttons = {}

        # 控件引用
        self.dashboard_tree = None
        self.dashboard_dir_container = None
        self.full_log_tree = None
        self.full_dirs_container = None

        self.watch_dirs_data = list(self.config.get("watch_dirs", []))

        # 3. 布局容器
        self.main_container = ctk.CTkFrame(self.window, corner_radius=0, fg_color=COLOR_BG)
        self.main_container.pack(fill="both", expand=True)

        # 侧边栏
        self.sidebar = ctk.CTkFrame(self.main_container, width=240, corner_radius=0, fg_color=COLOR_WHITE)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # 内容区域
        self.content_area = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True)

        # 4. 初始化界面
        self._setup_treeview_style()
        self.setup_sidebar()
        self.setup_pages()

        self.switch_to("dashboard")

    def _setup_treeview_style(self):
        """配置原生 Treeview 样式"""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview.Heading",
                        background="#F8F9FB",
                        foreground=COLOR_TEXT_MAIN,
                        relief="flat",
                        font=("Microsoft YaHei UI", 11, "bold"),
                        padding=(10, 8))

        style.configure("Treeview",
                        background=COLOR_WHITE,
                        foreground=COLOR_TEXT_SUB,
                        fieldbackground=COLOR_WHITE,
                        bordercolor=COLOR_WHITE,
                        borderwidth=0,
                        rowheight=40,
                        font=("Microsoft YaHei UI", 10))

        style.map("Treeview",
                  background=[('selected', '#E6F7FF')],
                  foreground=[('selected', COLOR_TEXT_MAIN)])

    def setup_sidebar(self):
        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(30, 30), padx=20, fill="x")

        ctk.CTkLabel(
            logo_frame,
            text="ZenFile",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color="#2b2b2b",
            compound="left"
        ).pack(side="left")

        # 导航区
        self.nav_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_container.pack(fill="x", pady=10)

        self.create_nav_btn("🏠  主页", "dashboard")
        self.create_nav_btn("📝  操作日志", "logs")
        self.create_nav_btn("📂  监控目录", "dirs")
        self.create_nav_btn("⚙️  系统设置", "settings")

        # 保存按钮
        save_btn = ctk.CTkButton(
            self.sidebar,
            text="保存配置",
            command=self.save,
            fg_color=COLOR_GREEN,
            hover_color="#26B074",
            height=40,
            corner_radius=6,
            font=("Microsoft YaHei UI", 14, "bold")
        )
        save_btn.pack(side="bottom", fill="x", padx=20, pady=30)

    def create_nav_btn(self, text, page_key):
        btn = ctk.CTkButton(
            self.nav_container,
            text=text,
            fg_color="transparent",
            text_color=COLOR_TEXT_SUB,
            hover_color="#F0F2F5",
            anchor="w",
            height=50,
            corner_radius=8,
            font=("Microsoft YaHei UI", 14),
            command=lambda: self.switch_to(page_key)
        )
        btn.pack(fill="x", pady=2, padx=15)
        self.nav_buttons[page_key] = btn

    def setup_pages(self):
        builders = {
            "dashboard": self.build_dashboard_page,
            "logs": self.build_logs_page,
            "dirs": self.build_dirs_page,
            "settings": self.build_settings_page
        }

        for key, builder in builders.items():
            frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
            builder(frame)
            self.pages[key] = frame

    def switch_to(self, page_key):
        if self.current_page:
            self.current_page.pack_forget()

        for key, btn in self.nav_buttons.items():
            if key == page_key:
                btn.configure(fg_color="#EBECEE", text_color="black")
            else:
                btn.configure(fg_color="transparent", text_color=COLOR_TEXT_SUB)

        frame = self.pages.get(page_key)
        if frame:
            frame.pack(fill="both", expand=True, padx=30, pady=30)
            self.current_page = frame

            # 切换页面时自动刷新对应数据
            if page_key == "dashboard":
                self.refresh_dashboard_logs()
                self.refresh_dashboard_dirs()
            elif page_key == "logs":
                self.refresh_full_logs()
            elif page_key == "dirs":
                self.refresh_dir_list_page()

    def create_card(self, parent, title=None):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color=COLOR_WHITE, border_width=1, border_color=COLOR_BORDER)
        if title:
            ctk.CTkLabel(card, text=title, font=("Microsoft YaHei UI", 16, "bold"), text_color="black").pack(anchor="w",
                                                                                                             padx=20,
                                                                                                             pady=(
                                                                                                             15, 5))
        return card


    def build_dashboard_page(self, parent):
        ctk.CTkLabel(parent, text="主页", font=("Microsoft YaHei UI", 24, "bold"), text_color="black").pack(anchor="w",
                                                                                                           pady=(0, 20))

        # Top Section
        top_section = ctk.CTkFrame(parent, fg_color="transparent")
        top_section.pack(fill="x", expand=False, pady=(0, 20))

        # Left Column
        left_col = ctk.CTkFrame(top_section, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # A. 操作中心
        op_card = self.create_card(left_col, "操作中心")
        op_card.pack(fill="x", pady=(0, 15))

        status_box = ctk.CTkFrame(op_card, fg_color="#FAFAFA", corner_radius=8, border_width=1, border_color="#EEEEEE")
        status_box.pack(fill="x", padx=20, pady=(10, 20))

        ctk.CTkLabel(status_box, text="运行状态", font=("Microsoft YaHei UI", 12), text_color="gray").pack(anchor="w",
                                                                                                       padx=15,
                                                                                                       pady=(10, 0))

        status_row = ctk.CTkFrame(status_box, fg_color="transparent")
        status_row.pack(fill="x", padx=15, pady=(5, 15))

        self.status_icon = ctk.CTkLabel(status_row, text="▶", font=("Arial", 28), text_color=COLOR_GREEN)
        self.status_icon.pack(side="left")

        self.status_text = ctk.CTkLabel(status_row, text="正在监控中", font=("Microsoft YaHei UI", 20, "bold"),
                                        text_color="black")
        self.status_text.pack(side="left", padx=10)

        # B. 快捷指令
        cmd_card = self.create_card(left_col, "快捷指令")
        cmd_card.pack(fill="x")

        btn_row = ctk.CTkFrame(cmd_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(
            btn_row, text="立即整理",
            command=self.run_now,
            fg_color=COLOR_BLUE, hover_color="#327AC0",
            height=45, font=("Microsoft YaHei UI", 13, "bold")
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            btn_row, text="撤销操作",
            command=self.undo,
            fg_color=COLOR_ORANGE, hover_color="#D98B34",
            height=45, font=("Microsoft YaHei UI", 13, "bold")
        ).pack(side="left", fill="x", expand=True, padx=(10, 0))

        # Right Column: C. 监控目录
        right_col = ctk.CTkFrame(top_section, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True)

        dir_card = self.create_card(right_col)
        dir_card.pack(fill="both", expand=True)

        dir_header = ctk.CTkFrame(dir_card, fg_color="transparent")
        dir_header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(dir_header, text="监控目录", font=("Microsoft YaHei UI", 16, "bold"), text_color="black").pack(
            side="left")
        ctk.CTkButton(dir_header, text="添加", command=self.add_dir, width=60, height=28, fg_color=COLOR_BLUE).pack(
            side="right")

        self.dashboard_dir_container = ctk.CTkScrollableFrame(dir_card, fg_color="transparent")
        self.dashboard_dir_container.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        # ---------------------------------------------------------
        # 下半部分：D. 最近活动 (Mini版)
        # ---------------------------------------------------------
        log_card = self.create_card(parent)
        log_card.pack(fill="both", expand=True)

        log_header = ctk.CTkFrame(log_card, fg_color="transparent")
        log_header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(log_header, text="最近活动", font=("Microsoft YaHei UI", 16, "bold"), text_color="black").pack(
            side="left")
        ctk.CTkButton(log_header, text="刷新", command=self.refresh_dashboard_logs, width=60, height=28,
                      fg_color="transparent", border_width=1, text_color="gray").pack(side="right")

        table_frame = ctk.CTkFrame(log_card, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.dashboard_tree = self._create_scrolling_treeview(table_frame, height=6)

        self._update_status_display()

    # ================= 操作日志页面 (Full Logs) =================

    def build_logs_page(self, parent):
        ctk.CTkLabel(parent, text="操作日志", font=("Microsoft YaHei UI", 24, "bold"), text_color="black").pack(anchor="w",
                                                                                                            pady=(
                                                                                                            0, 20))

        card = self.create_card(parent)
        card.pack(fill="both", expand=True)

        # 头部
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(header, text="所有历史记录", font=("Microsoft YaHei UI", 16, "bold"), text_color="black").pack(
            side="left")
        ctk.CTkButton(header, text="刷新列表", command=self.refresh_full_logs, width=80, fg_color="transparent",
                      border_width=1, text_color="gray").pack(side="right")

        # 表格区域
        table_frame = ctk.CTkFrame(card, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # 使用复用函数创建全尺寸表格 (height 设大一点)
        self.full_log_tree = self._create_scrolling_treeview(table_frame, height=15)

    def _create_scrolling_treeview(self, parent, height):
        columns = ("time", "type", "source", "target")
        tree = ttk.Treeview(parent, columns=columns, show="headings", style="Treeview", height=height)

        tree.column("time", width=180, anchor="w")
        tree.column("type", width=80, anchor="center")
        tree.column("source", width=350, anchor="w")
        tree.column("target", width=350, anchor="w")

        tree.heading("time", text="时间")
        tree.heading("type", text="类型")
        tree.heading("source", text="源文件")
        tree.heading("target", text="目标文件")

        # 滚动条 (使用 CTk 样式)
        ysb = ctk.CTkScrollbar(parent, orientation="vertical", command=tree.yview)
        xsb = ctk.CTkScrollbar(parent, orientation="horizontal", command=tree.xview)

        tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)

        ysb.pack(side="right", fill="y")
        xsb.pack(side="bottom", fill="x")
        tree.pack(side="left", fill="both", expand=True)
        return tree

    # ================= 监控目录页面 (Full Dirs) =================

    def build_dirs_page(self, parent):
        ctk.CTkLabel(parent, text="目录管理", font=("Microsoft YaHei UI", 24, "bold"), text_color="black").pack(anchor="w",
                                                                                                            pady=(
                                                                                                            0, 20))

        card = self.create_card(parent)
        card.pack(fill="both", expand=True)

        # 头部
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(header, text="监控目录列表", font=("Microsoft YaHei UI", 16, "bold"), text_color="black").pack(
            side="left")

        ctk.CTkButton(
            header, text="+ 添加目录", command=self.add_dir,
            fg_color=COLOR_BLUE, width=100
        ).pack(side="right")

        # 列表区域 (使用 ScrollableFrame)
        self.full_dirs_container = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.full_dirs_container.pack(fill="both", expand=True, padx=10, pady=(0, 20))

    # ================= 偏好设置页面 =================

    def build_settings_page(self, parent):
        ctk.CTkLabel(parent, text="偏好设置", font=("Microsoft YaHei UI", 24, "bold"), text_color="black").pack(anchor="w",
                                                                                                            pady=(
                                                                                                            0, 20))
        card = self.create_card(parent)
        card.pack(fill="x")

        self.v_run = ctk.BooleanVar(value=is_autorun_enabled())
        sw = ctk.CTkSwitch(
            card, text="开机自动启动 ZenFile", variable=self.v_run,
            command=self.tog_run, font=("Microsoft YaHei UI", 14),
            progress_color=COLOR_GREEN
        )
        sw.pack(anchor="w", padx=30, pady=30)

        hk_frame = ctk.CTkFrame(card, fg_color="transparent")
        hk_frame.pack(fill="x", padx=30, pady=(0, 30))

        ctk.CTkLabel(hk_frame, text="全局快捷键:", font=("Microsoft YaHei UI", 14)).pack(side="left")
        hk_wrapper = ctk.CTkFrame(hk_frame, fg_color="#F0F2F5", corner_radius=6, height=36, width=200)
        hk_wrapper.pack(side="left", padx=15)
        hk_wrapper.pack_propagate(False)

        self.hk = HotkeyRecorder(hk_wrapper, default_value=self.config.get("hotkey", "<ctrl>+<alt>+z"))
        self.hk.pack(fill="both", expand=True, padx=10, pady=2)
        self.hk.configure(fg_color="#F0F2F5", text_color=COLOR_TEXT_MAIN, border_width=0)

    # ================= 逻辑处理与刷新 =================

    def _update_status_display(self):
        if hasattr(self, 'status_text'):
            is_paused = self.organizer.paused
            if is_paused:
                self.status_icon.configure(text="⏸", text_color="gray")
                self.status_text.configure(text="已暂停服务", text_color="gray")
            else:
                self.status_icon.configure(text="▶", text_color=COLOR_GREEN)
                self.status_text.configure(text="正在监控中", text_color="black")

    # --- 日志刷新 ---
    def refresh_dashboard_logs(self):
        self._refresh_logs_common(self.dashboard_tree, limit=10)

    def refresh_full_logs(self):
        self._refresh_logs_common(self.full_log_tree, limit=100)

    def _refresh_logs_common(self, tree_widget, limit):
        if not tree_widget: return
        for item in tree_widget.get_children():
            tree_widget.delete(item)
        try:
            history = HistoryManager.load_history()
            if history:
                for rec in reversed(history[-limit:]):
                    tree_widget.insert("", "end", values=(
                        rec.get("time", ""), "文件", rec.get("source", ""), rec.get("target", "")
                    ))
        except Exception as e:
            print(f"日志加载错误: {e}")

    # --- 目录刷新 ---
    def refresh_dashboard_dirs(self):
        self._refresh_dirs_common(self.dashboard_dir_container)

    def refresh_dir_list_page(self):
        self._refresh_dirs_common(self.full_dirs_container)

    def _refresh_dirs_common(self, container_widget):
        if not container_widget: return

        # 清空
        for widget in container_widget.winfo_children():
            widget.destroy()

        if not self.watch_dirs_data:
            ctk.CTkLabel(container_widget, text="暂无监控目录", text_color="gray").pack(pady=20)
            return

        # 渲染列表项
        for path in self.watch_dirs_data:
            row = ctk.CTkFrame(container_widget, fg_color="#FAFAFA", corner_radius=6, border_width=1,
                               border_color="#EEEEEE")
            row.pack(fill="x", pady=4, padx=5)

            ctk.CTkLabel(row, text="📂", font=("Segoe UI Emoji", 14), text_color="#FBC02D").pack(side="left",
                                                                                                 padx=(10, 5))

            # 路径截断显示 (防止撑破UI)
            display_path = path
            if len(path) > 40:
                display_path = path[:15] + "..." + path[-20:]

            ctk.CTkLabel(row, text=display_path, font=("Consolas", 12), text_color="#333").pack(side="left")

            ctk.CTkButton(
                row, text="删除", width=50, height=24,
                fg_color=COLOR_RED, hover_color="#D9363E",
                font=("Microsoft YaHei UI", 11),
                command=lambda p=path: self.remove_dir(p)
            ).pack(side="right", padx=10, pady=8)

    # --- 动作逻辑 ---

    def add_dir(self):
        p = filedialog.askdirectory()
        if p and p not in self.watch_dirs_data:
            self.watch_dirs_data.append(p)
            # 添加后同时刷新两个界面（如果它们已被创建）
            self.refresh_dashboard_dirs()
            self.refresh_dir_list_page()

    def remove_dir(self, path_to_remove):
        if path_to_remove in self.watch_dirs_data:
            self.watch_dirs_data.remove(path_to_remove)
            # 删除后同时刷新两个界面
            self.refresh_dashboard_dirs()
            self.refresh_dir_list_page()

    def run_now(self):
        try:
            c = self.organizer.run_now()
            messagebox.showinfo("完成", f"已立即处理 {c} 个文件")
            self.refresh_dashboard_logs()
            self.refresh_full_logs()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def undo(self):
        try:
            s, m = self.organizer.undo_last_action()
            messagebox.showinfo("操作结果", m)
            self.refresh_dashboard_logs()
            self.refresh_full_logs()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def tog_run(self):
        target_state = self.v_run.get()
        if not set_autorun(target_state):
            self.v_run.set(not target_state)
            messagebox.showerror("权限错误", "无法修改自启设置，请尝试以管理员身份运行程序。")

    def save(self):
        hk = self.hk.get_hotkey()
        self.config.update({"watch_dirs": self.watch_dirs_data, "hotkey": hk})
        try:
            save_config(self.config)
            self.organizer.reload_config(self.config)
            self.monitor_mgr.update_watches(self.watch_dirs_data)
            self.hotkey_mgr.restart(hk)
            self._update_status_display()
            messagebox.showinfo("保存成功", "配置已更新并立即生效")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))