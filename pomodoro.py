import tkinter as tk
import sys
import os
import platform

# ── 预设时长（分钟） ──
WORK_MIN = 25
SHORT_BREAK_MIN = 5
LONG_BREAK_MIN = 15
SESSIONS_BEFORE_LONG_BREAK = 4  # 完成 4 个番茄后进入长休息

# ── 各模式对应的秒数 ──
DURATIONS = {
    "work": WORK_MIN * 60,
    "short_break": SHORT_BREAK_MIN * 60,
    "long_break": LONG_BREAK_MIN * 60,
}

COLORS = {
    "work": "#E74C3C",
    "short_break": "#2ECC71",
    "long_break": "#3498DB",
    "bg": "#1E1E2E",
    "surface": "#2D2D44",
    "text": "#EEEEEE",
    "text_dim": "#8888AA",
    "btn_text": "#FFFFFF",
}

# 按钮按下时的深色背景
ACTIVE_BG = {
    "work": "#C0392B",
    "short_break": "#27AE60",
    "long_break": "#2980B9",
}

# 模式在界面上的显示标签
MODE_LABELS = {
    "work": "WORK",
    "short_break": "SHORT BREAK",
    "long_break": "LONG BREAK",
}


def _play_beep():
    """跨平台提示音：Windows 用 winsound，其他平台 fallback 到 ASCII bell。"""
    if platform.system() == "Windows":
        try:
            import winsound

            winsound.MessageBeep(0xFFFFFFFF)
        except Exception:
            sys.stdout.write("\a")
    else:
        sys.stdout.write("\a")
        sys.stdout.flush()


class PomodoroApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Pomodoro Timer")
        # 先设定几何尺寸再居中
        self.geometry("380x420")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])
        self._center_window()

        # ── 加载图标（如果存在） ──
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "tomato.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        # ── 状态变量 ──
        self.mode = "work"
        self.sessions_completed = 0
        self.remaining = DURATIONS["work"]
        self.total_seconds = DURATIONS["work"]
        self.running = False
        self.after_id = None  # 计时器 after 句柄
        self.auto_start_id = None  # 自动开始延迟句柄
        self.always_on_top = tk.BooleanVar(value=True)
        self.auto_start = tk.BooleanVar(value=True)

        self.attributes("-topmost", True)

        self._build_ui()
        self._bind_keys()
        self._update_display()

    # ═══════════════════════════════════════════════
    #  窗口与快捷键
    # ═══════════════════════════════════════════════

    def _center_window(self):
        """将窗口放置到屏幕中央。需要先调用 geometry() 设定尺寸。"""
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")

    def _bind_keys(self):
        """绑定全局键盘快捷键。"""
        self.bind_all("<space>", lambda e: self._toggle_start_pause())
        self.bind_all("<Key-r>", lambda e: self._reset())
        self.bind_all("<Key-s>", lambda e: self._skip())
        self.bind_all("<Key-t>", lambda e: self._toggle_always_on_top())

    # ═══════════════════════════════════════════════
    #  UI 构建
    # ═══════════════════════════════════════════════

    def _build_ui(self):
        # 标题
        title = tk.Label(
            self,
            text="Pomodoro Timer",
            font=("Segoe UI", 16, "bold"),
            fg=COLORS["text"],
            bg=COLORS["bg"],
        )
        title.pack(pady=(20, 8))

        # 模式标签
        self.mode_label = tk.Label(
            self,
            text="WORK",
            font=("Segoe UI", 11, "bold"),
            fg=COLORS["btn_text"],
            bg=COLORS["work"],
            padx=18,
            pady=4,
        )
        self.mode_label.pack(pady=(0, 10))

        # 倒计时显示
        timer_frame = tk.Frame(self, bg=COLORS["surface"], highlightthickness=0)
        timer_frame.pack(pady=6)

        self.timer_label = tk.Label(
            timer_frame,
            text="25:00",
            font=("Consolas", 48, "bold"),
            fg=COLORS["text"],
            bg=COLORS["surface"],
            padx=40,
            pady=16,
        )
        self.timer_label.pack()

        # 番茄完成进度（● = 已完成）
        self.progress_label = tk.Label(
            self,
            text="",
            font=("Segoe UI", 13),
            fg=COLORS["text_dim"],
            bg=COLORS["bg"],
        )
        self.progress_label.pack(pady=(8, 0))

        # 按钮区域
        btn_frame = tk.Frame(self, bg=COLORS["bg"])
        btn_frame.pack(pady=(14, 6))

        self.start_btn = tk.Button(
            btn_frame,
            text="Start",
            command=self._toggle_start_pause,
            font=("Segoe UI", 12, "bold"),
            fg=COLORS["btn_text"],
            bg=COLORS["work"],
            activebackground="#C0392B",
            activeforeground="white",
            relief="flat",
            padx=28,
            pady=6,
            cursor="hand2",
        )
        self.start_btn.pack(side="left", padx=6)

        self.reset_btn = tk.Button(
            btn_frame,
            text="Reset",
            command=self._reset,
            font=("Segoe UI", 12),
            fg=COLORS["text"],
            bg=COLORS["surface"],
            activebackground="#3D3D54",
            activeforeground="white",
            relief="flat",
            padx=28,
            pady=6,
            cursor="hand2",
        )
        self.reset_btn.pack(side="left", padx=6)

        # 时长提示（高亮当前模式）
        hints = tk.Frame(self, bg=COLORS["bg"])
        hints.pack(pady=(10, 0))

        self.work_hint = self._make_hint(hints, "Work", WORK_MIN, 0)
        self.short_hint = self._make_hint(hints, "Short Break", SHORT_BREAK_MIN, 1)
        self.long_hint = self._make_hint(hints, "Long Break", LONG_BREAK_MIN, 2)

        # 底部栏
        bottom = tk.Frame(self, bg=COLORS["bg"])
        bottom.pack(side="bottom", fill="x", padx=16, pady=10)

        self.skip_btn = tk.Button(
            bottom,
            text="Skip",
            command=self._skip,
            font=("Segoe UI", 10),
            fg=COLORS["text_dim"],
            bg=COLORS["bg"],
            activebackground=COLORS["surface"],
            activeforeground=COLORS["text"],
            relief="flat",
            padx=12,
            pady=2,
            cursor="hand2",
        )
        self.skip_btn.pack(side="left")

        # 始终置顶复选框
        cb = tk.Checkbutton(
            bottom,
            text="Always on top",
            variable=self.always_on_top,
            command=self._toggle_always_on_top,
            font=("Segoe UI", 9),
            fg=COLORS["text_dim"],
            bg=COLORS["bg"],
            selectcolor=COLORS["surface"],
            activebackground=COLORS["bg"],
            activeforeground=COLORS["text"],
            cursor="hand2",
        )
        cb.pack(side="right")

        # 自动开始下一阶段复选框
        auto_cb = tk.Checkbutton(
            bottom,
            text="Auto-start next",
            variable=self.auto_start,
            font=("Segoe UI", 9),
            fg=COLORS["text_dim"],
            bg=COLORS["bg"],
            selectcolor=COLORS["surface"],
            activebackground=COLORS["bg"],
            activeforeground=COLORS["text"],
            cursor="hand2",
        )
        auto_cb.pack(side="right", padx=(0, 8))

    def _make_hint(self, parent, text, minutes, column):
        """在 hints frame 中创建一个时长标签。"""
        lbl = tk.Label(
            parent,
            text=f"{text}\n{minutes} min",
            font=("Segoe UI", 9),
            fg=COLORS["text_dim"],
            bg=COLORS["bg"],
            justify="center",
            padx=10,
        )
        lbl.grid(row=0, column=column, padx=8)
        return lbl

    # ═══════════════════════════════════════════════
    #  计时引擎
    # ═══════════════════════════════════════════════

    def _toggle_start_pause(self):
        if self.running:
            self._pause()
        else:
            self._start()

    def _start(self):
        if self.running:
            return
        # 取消可能存在的自动启动延迟
        if self.auto_start_id:
            self.after_cancel(self.auto_start_id)
            self.auto_start_id = None
        self.running = True
        self.start_btn.config(text="Pause", bg="#F39C12", activebackground="#D68910")
        self._tick()

    def _pause(self):
        self.running = False
        self.start_btn.config(
            text="Start",
            bg=COLORS[self.mode],
            activebackground=ACTIVE_BG[self.mode],
        )
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        if self.auto_start_id:
            self.after_cancel(self.auto_start_id)
            self.auto_start_id = None

    def _tick(self):
        """每秒回调：递减剩余秒数并刷新界面。"""
        if not self.running:
            return

        self.remaining -= 1
        self._update_display()
        self._update_title()

        if self.remaining <= 0:
            self._on_timer_end()
        else:
            self.after_id = self.after(1000, self._tick)

    def _on_timer_end(self):
        """计时结束时：播放提示音并切换到下一阶段。"""
        self.running = False
        self.after_id = None

        _play_beep()

        if self.mode == "work":
            self.sessions_completed += 1
            if self.sessions_completed >= SESSIONS_BEFORE_LONG_BREAK:
                self._switch_mode("long_break")
                self.sessions_completed = 0
            else:
                self._switch_mode("short_break")
        else:
            self._switch_mode("work")

        self._update_display()
        self._update_title()

        # 如果开启了自动开始，延迟 0.8 秒后自动进入下一阶段
        if self.auto_start.get():
            self.auto_start_id = self.after(800, self._start)

    def _switch_mode(self, new_mode):
        self.mode = new_mode
        self.total_seconds = DURATIONS[new_mode]
        self.remaining = self.total_seconds
        self.start_btn.config(
            text="Start",
            bg=COLORS[new_mode],
            activebackground=ACTIVE_BG[new_mode],
        )
        self._update_mode_label()
        self._update_hints()

    def _reset(self):
        """重置当前阶段的计时。"""
        self._pause()
        self.remaining = self.total_seconds
        self._update_display()
        self._update_title()

    def _skip(self):
        """跳过当前阶段。"""
        self._pause()
        self.remaining = 0
        self._on_timer_end()

    # ═══════════════════════════════════════════════
    #  界面刷新
    # ═══════════════════════════════════════════════

    def _update_display(self):
        mins, secs = divmod(self.remaining, 60)
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")

        # 用 ●/○ 显示已完成番茄数
        dots = []
        for i in range(SESSIONS_BEFORE_LONG_BREAK):
            dots.append("●" if i < self.sessions_completed else "○")
        self.progress_label.config(text="  ".join(dots))

    def _update_title(self):
        """任务栏标题显示当前倒计时和模式。"""
        mins, secs = divmod(self.remaining, 60)
        name = MODE_LABELS.get(self.mode, "Pomo").title()
        self.title(f"{mins:02d}:{secs:02d} - {name} - Pomodoro")

    def _update_mode_label(self):
        self.mode_label.config(
            text=MODE_LABELS.get(self.mode, ""), bg=COLORS[self.mode]
        )

    def _update_hints(self):
        """高亮当前模式对应的时长提示。"""
        order = ["work", "short_break", "long_break"]
        hints = [self.work_hint, self.short_hint, self.long_hint]
        for i, h in enumerate(hints):
            if order[i] == self.mode:
                h.config(fg=COLORS[self.mode])
            else:
                h.config(fg=COLORS["text_dim"])

    def _toggle_always_on_top(self):
        self.attributes("-topmost", self.always_on_top.get())


if __name__ == "__main__":
    app = PomodoroApp()
    app.mainloop()
