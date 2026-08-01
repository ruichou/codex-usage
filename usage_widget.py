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
        self.root.geometry("300x88+20+20")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=self.transparent)
        try:
            self.root.attributes("-transparentcolor", self.transparent)
        except tk.TclError:
            pass
        self._drag_offset = (0, 0)
        self._progress_width = 0
        self._progress_color = "#45d483"
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.refresh()

    def _build_ui(self):
        self.canvas = tk.Canvas(self.root, width=300, height=88, bg=self.transparent, highlightthickness=0)
        self.canvas.pack()
        # Layered bevel: shadow, lower rim, body, top gloss.
        self._round_rect(3, 4, 297, 87, 27, fill="#080b10", outline="")
        self._round_rect(2, 2, 296, 84, 26, fill="#202938", outline="#2e3a4b")
        self._round_rect(4, 4, 294, 82, 24, fill=self.surface, outline="")
        self.canvas.create_line(28, 5, 266, 5, fill="#4a5668", width=1)

        self.percent = tk.Label(self.root, text="读取中…", bg=self.surface, fg="#f4f7fb", font=("Segoe UI", 22, "bold"))
        self.percent.place(x=18, y=12)
        self.plan = tk.Label(self.root, text="正在连接…", bg=self.surface, fg="#a7b1c2", font=("Segoe UI", 8))
        self.plan.place(x=112, y=14)
        self.reset = tk.Label(self.root, text="", bg=self.surface, fg="#a7b1c2", font=("Segoe UI", 8))
        self.reset.place(x=112, y=32)
        self.bar = tk.Canvas(self.root, width=264, height=18, bg=self.surface, highlightthickness=0)
        self.bar.place(x=18, y=55)
        self.bar.create_rectangle(0, 0, 264, 18, fill="#2a3545", outline="")

        self.minimize = tk.Label(self.root, text="−", bg=self.surface, fg="#9ba7b8", activebackground="#2d394a", activeforeground="#ffffff", font=("Segoe UI", 11), cursor="hand2")
        self.minimize.place(x=258, y=10, width=16, height=18)
        self.close = tk.Label(self.root, text="×", bg=self.surface, fg="#9ba7b8", activebackground="#672f3a", activeforeground="#ffffff", font=("Segoe UI", 11), cursor="hand2")
        self.close.place(x=276, y=10, width=16, height=18)
        self.minimize.bind("<Button-1>", lambda _event: self.root.iconify())
        self.close.bind("<Button-1>", lambda _event: self.root.destroy())
        for widget in (self.canvas, self.percent, self.plan, self.reset):
            widget.bind("<ButtonPress-1>", self._drag_start)
            widget.bind("<B1-Motion>", self._drag_move)

    def _round_rect(self, x1, y1, x2, y2, radius, **kwargs):
        self.canvas.create_arc(x1, y1, x1 + radius * 2, y1 + radius * 2, start=90, extent=90, style="pieslice", **kwargs)
        self.canvas.create_arc(x2 - radius * 2, y1, x2, y1 + radius * 2, start=0, extent=90, style="pieslice", **kwargs)
        self.canvas.create_arc(x1, y2 - radius * 2, x1 + radius * 2, y2, start=180, extent=90, style="pieslice", **kwargs)
        self.canvas.create_arc(x2 - radius * 2, y2 - radius * 2, x2, y2, start=270, extent=90, style="pieslice", **kwargs)
        self.canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, **kwargs)
        self.canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, **kwargs)

    def _drag_start(self, event):
        self._drag_offset = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())

    def _drag_move(self, event):
        self.root.geometry(f"+{event.x_root - self._drag_offset[0]}+{event.y_root - self._drag_offset[1]}")

    def refresh(self):
        self.plan.config(text="正在读取…")
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
        self.percent.config(text=f"{snapshot.remaining_percent}%", fg=color)
        self._progress_width = int(264 * snapshot.remaining_percent / 100)
        self._progress_color = color
        self._draw_bar()
        self.plan.config(text=f"{snapshot.plan} 套餐 · {'可用' if snapshot.allowed else '已达到限制'}")
        self.reset.config(text=format_reset(reset_after))

    def _show_error(self, message: str):
        self.percent.config(text="--", fg="#ef6b73")
        self._progress_width = 0
        self._draw_bar()
        self.plan.config(text="暂时无法读取 Codex 用量")
        self.reset.config(text=message[:28] or "请确认 Codex 已登录")

    def _draw_bar(self):
        self.bar.delete("all")
        self.bar.create_rectangle(0, 0, 264, 18, fill="#2a3545", outline="")
        if self._progress_width <= 0:
            return
        self.bar.create_rectangle(0, 0, self._progress_width, 18, fill=self._progress_color, outline="")
        self.bar.create_line(3, 2, max(3, self._progress_width - 3), 2, fill="#ffffff", stipple="gray50")


def main():
    root = tk.Tk()
    UsageWidget(root)
    root.mainloop()


if __name__ == "__main__":
    main()
