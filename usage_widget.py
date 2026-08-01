import json
import os
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
import tkinter as tk

USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"
REFRESH_MS = 30_000


@dataclass(frozen=True)
class UsageSnapshot:
    plan: str
    remaining_percent: int
    reset_at: datetime | None
    allowed: bool


def parse_usage(data: dict) -> UsageSnapshot:
    window = ((data.get("rate_limit") or {}).get("primary_window") or {})
    used = max(0, min(100, int(window.get("used_percent", 100))))
    plan = str(data.get("plan_type") or "unknown").replace("_", " ").title()
    reset_at = window.get("reset_at")
    reset = datetime.fromtimestamp(float(reset_at), timezone.utc) if reset_at else None
    return UsageSnapshot(plan, 100 - used, reset, bool((data.get("rate_limit") or {}).get("allowed", False)))


def format_reset(seconds: int | float | None) -> str:
    if seconds is None:
        return "重置时间未知"
    seconds = max(0, int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes = seconds // 60
    return f"{days}天 {hours}小时后重置" if days else f"{hours}小时 {minutes}分钟后重置"


def fetch_usage() -> tuple[UsageSnapshot, int | None]:
    with open(os.path.join(os.path.expanduser("~"), ".codex", "auth.json"), encoding="utf-8") as handle:
        auth = json.load(handle)
    tokens = auth.get("tokens") or {}
    if not tokens.get("access_token") or not tokens.get("account_id"):
        raise RuntimeError("未找到 Codex 登录状态")
    request = urllib.request.Request(USAGE_URL, headers={
        "Authorization": f"Bearer {tokens['access_token']}",
        "ChatGPT-Account-ID": tokens["account_id"],
        "Accept": "application/json",
        "User-Agent": "codex-usage-widget/1.0",
    })
    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.load(response)
    window = ((data.get("rate_limit") or {}).get("primary_window") or {})
    return parse_usage(data), window.get("reset_after_seconds")


class UsageWidget:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.surface = "#171c25"
        self.transparent = "#05080d"
        self.root.overrideredirect(True)
        self.root.geometry("96x96+20+20")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=self.transparent)
        try:
            self.root.attributes("-transparentcolor", self.transparent)
        except tk.TclError:
            pass
        self._drag_offset = (0, 0)
        self._progress = 0
        self._progress_color = "#45d483"
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.refresh()

    def _build_ui(self):
        self.canvas = tk.Canvas(self.root, width=96, height=96, bg=self.transparent, highlightthickness=0)
        self.canvas.pack()
        self._draw_sphere()

        self.percent = tk.Label(self.root, text="--", bg=self.surface, fg="#f4f7fb", font=("Segoe UI", 16, "bold"))
        self.percent.place(x=20, y=32, width=56, height=23)
        self.plan = tk.Label(self.root, text="读取中…", bg=self.surface, fg="#a7b1c2", font=("Segoe UI", 6))
        self.plan.place(x=12, y=63, width=72, height=10)
        self.reset = tk.Label(self.root, text="", bg=self.surface, fg="#7e8a9d", font=("Segoe UI", 6))
        self.reset.place(x=8, y=76, width=80, height=9)

        self.minimize = tk.Label(self.root, text="−", bg=self.surface, fg="#aab5c5", activebackground="#2d394a", activeforeground="#ffffff", font=("Segoe UI", 8), cursor="hand2")
        self.minimize.place(x=62, y=13, width=13, height=13)
        self.close = tk.Label(self.root, text="×", bg=self.surface, fg="#aab5c5", activebackground="#672f3a", activeforeground="#ffffff", font=("Segoe UI", 8), cursor="hand2")
        self.close.place(x=76, y=13, width=13, height=13)
        self.minimize.bind("<Button-1>", lambda _event: self.root.iconify())
        self.close.bind("<Button-1>", lambda _event: self.root.destroy())
        for widget in (self.canvas, self.percent, self.plan, self.reset):
            widget.bind("<ButtonPress-1>", self._drag_start)
            widget.bind("<B1-Motion>", self._drag_move)

    def _draw_sphere(self):
        self.canvas.delete("all")
        self.canvas.create_oval(5, 7, 93, 95, fill="#080b10", outline="")
        self.canvas.create_oval(2, 2, 94, 94, fill="#202938", outline="#3a485d", width=1)
        self.canvas.create_oval(6, 6, 90, 90, fill=self.surface, outline="")
        self.canvas.create_arc(12, 9, 84, 81, start=210, extent=125, style="arc", outline="#526078", width=2)
        self.canvas.create_arc(10, 10, 86, 86, start=90, extent=359, style="arc", outline="#2a3545", width=7)
        if self._progress > 0:
            self.canvas.create_arc(10, 10, 86, 86, start=90, extent=-3.6 * self._progress, style="arc", outline=self._progress_color, width=7)

    def _drag_start(self, event):
        self._drag_offset = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())

    def _drag_move(self, event):
        self.root.geometry(f"+{event.x_root - self._drag_offset[0]}+{event.y_root - self._drag_offset[1]}")

    def refresh(self):
        self.plan.config(text="读取中…")
        threading.Thread(target=self._read_in_background, daemon=True).start()
        self.root.after(REFRESH_MS, self.refresh)

    def _read_in_background(self):
        try:
            snapshot, reset_after = fetch_usage()
            self.root.after(0, lambda: self._show_snapshot(snapshot, reset_after))
        except (OSError, ValueError, urllib.error.URLError, RuntimeError, KeyError) as error:
            self.root.after(0, lambda: self._show_error(str(error)))

    def _show_snapshot(self, snapshot: UsageSnapshot, reset_after: int | None):
        remaining = snapshot.remaining_percent
        color = "#45d483" if remaining >= 70 else "#4da3ff" if remaining >= 30 else "#f2b84b" if remaining >= 10 else "#ef6b73"
        self.percent.config(text=f"{remaining}%", fg=color)
        self._progress = remaining
        self._progress_color = color
        self._draw_sphere()
        self.plan.config(text=f"{snapshot.plan} · {'可用' if snapshot.allowed else '受限'}")
        self.reset.config(text=format_reset(reset_after))

    def _show_error(self, message: str):
        self.percent.config(text="--", fg="#ef6b73")
        self._progress = 0
        self._draw_sphere()
        self.plan.config(text="暂时无法读取")
        self.reset.config(text=message[:16] or "请检查登录")


def main():
    root = tk.Tk()
    UsageWidget(root)
    root.mainloop()


if __name__ == "__main__":
    main()
