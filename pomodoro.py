import tkinter as tk
import winsound
import os

WORK_MIN = 25
SHORT_BREAK_MIN = 5
LONG_BREAK_MIN = 15
SESSIONS_BEFORE_LONG_BREAK = 4

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


class PomodoroApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Pomodoro Timer")
        self.geometry("380x420")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])

        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "tomato.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        # ── State ──
        self.mode = "work"
        self.sessions_completed = 0
        self.remaining = WORK_MIN * 60
        self.total_seconds = WORK_MIN * 60
        self.running = False
        self.after_id = None
        self.auto_start_id = None
        self.always_on_top = tk.BooleanVar(value=True)
        self.auto_start = tk.BooleanVar(value=True)

        self.attributes("-topmost", True)

        self._build_ui()
        self._update_display()

    # ═══════════════════════════════════════════════
    #  UI Construction
    # ═══════════════════════════════════════════════

    def _build_ui(self):
        # Title
        title = tk.Label(
            self,
            text="Pomodoro Timer",
            font=("Segoe UI", 16, "bold"),
            fg=COLORS["text"],
            bg=COLORS["bg"],
        )
        title.pack(pady=(20, 8))

        # Mode badge
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

        # Timer display
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

        # Progress indicator
        self.progress_label = tk.Label(
            self,
            text="",
            font=("Segoe UI", 13),
            fg=COLORS["text_dim"],
            bg=COLORS["bg"],
        )
        self.progress_label.pack(pady=(8, 0))

        # Buttons
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

        # Session duration hints
        hints = tk.Frame(self, bg=COLORS["bg"])
        hints.pack(pady=(10, 0))

        self._make_hint(hints, "Work", WORK_MIN, COLORS["work"], 0)
        self._make_hint(hints, "Short Break", SHORT_BREAK_MIN, COLORS["short_break"], 1)
        self._make_hint(hints, "Long Break", LONG_BREAK_MIN, COLORS["long_break"], 2)

        self.work_hint = hints.winfo_children()[0]
        self.short_hint = hints.winfo_children()[1]
        self.long_hint = hints.winfo_children()[2]

        # Bottom bar: skip button + always-on-top toggle
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

        # auto-start toggle
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

    def _make_hint(self, parent, text, minutes, color, col):
        lbl = tk.Label(
            parent,
            text=f"{text}\n{minutes} min",
            font=("Segoe UI", 9),
            fg=COLORS["text_dim"],
            bg=COLORS["bg"],
            justify="center",
            padx=10,
        )
        lbl.grid(row=0, column=col, padx=8)
        return lbl

    # ═══════════════════════════════════════════════
    #  Timer Engine
    # ═══════════════════════════════════════════════

    def _toggle_start_pause(self):
        if self.running:
            self._pause()
        else:
            self._start()

    def _start(self):
        if self.running:
            return
        if self.auto_start_id:
            self.after_cancel(self.auto_start_id)
            self.auto_start_id = None
        self.running = True
        self.start_btn.config(text="Pause", bg="#F39C12", activebackground="#D68910")
        self._tick()

    def _pause(self):
        self.running = False
        self.start_btn.config(text="Start", bg=COLORS[self._mode_key()], activebackground=self._active_bg())
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        if self.auto_start_id:
            self.after_cancel(self.auto_start_id)
            self.auto_start_id = None

    def _tick(self):
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
        self.running = False
        self.after_id = None

        try:
            winsound.MessageBeep(0xFFFFFFFF)
        except Exception:
            pass

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

        if self.auto_start.get():
            self.auto_start_id = self.after(800, self._start)

    def _switch_mode(self, new_mode):
        self.mode = new_mode
        self.total_seconds = self._duration_for(new_mode)
        self.remaining = self.total_seconds
        self.start_btn.config(text="Start", bg=COLORS[self._mode_key()], activebackground=self._active_bg())
        self._update_mode_label()
        self._update_hints()

    def _reset(self):
        self._pause()
        self.remaining = self.total_seconds
        self._update_display()
        self._update_title()

    def _skip(self):
        self._pause()
        self.remaining = 0
        self._on_timer_end()

    # ═══════════════════════════════════════════════
    #  Helpers
    # ═══════════════════════════════════════════════

    def _mode_key(self):
        if self.mode == "work":
            return "work"
        elif self.mode == "short_break":
            return "short_break"
        return "long_break"

    def _duration_for(self, mode):
        if mode == "work":
            return WORK_MIN * 60
        elif mode == "short_break":
            return SHORT_BREAK_MIN * 60
        return LONG_BREAK_MIN * 60

    def _active_bg(self):
        mapping = {"work": "#C0392B", "short_break": "#27AE60", "long_break": "#2980B9"}
        return mapping.get(self._mode_key(), "#C0392B")

    def _update_display(self):
        mins, secs = divmod(self.remaining, 60)
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")

        dots = []
        for i in range(SESSIONS_BEFORE_LONG_BREAK):
            if i < self.sessions_completed:
                dots.append("●")
            else:
                dots.append("○")
        self.progress_label.config(text="  ".join(dots))

    def _update_title(self):
        mins, secs = divmod(self.remaining, 60)
        mode_names = {"work": "Work", "short_break": "Break", "long_break": "Long Break"}
        name = mode_names.get(self.mode, "Pomo")
        self.title(f"{mins:02d}:{secs:02d} - {name} - Pomodoro")

    def _update_mode_label(self):
        labels = {"work": "WORK", "short_break": "SHORT BREAK", "long_break": "LONG BREAK"}
        self.mode_label.config(text=labels.get(self.mode, ""), bg=COLORS[self._mode_key()])

    def _update_hints(self):
        mapping = {"work": 0, "short_break": 1, "long_break": 2}
        active_idx = mapping.get(self.mode, -1)
        hints = [self.work_hint, self.short_hint, self.long_hint]
        for i, h in enumerate(hints):
            if i == active_idx:
                h.config(fg=COLORS[self._mode_key()])
            else:
                h.config(fg=COLORS["text_dim"])

    def _toggle_always_on_top(self):
        self.attributes("-topmost", self.always_on_top.get())


if __name__ == "__main__":
    app = PomodoroApp()
    app.mainloop()
