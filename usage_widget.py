import json
import os
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
import tkinter as tk
from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont, ImageTk

USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"
REFRESH_MS = 30_000
WIDGET_SIZE = 180
SPHERE_BOX = (10, 10, 170, 170)
TEXT_RENDERER = "pillow"
RENDER_SCALE = 4
ANIMATION_MS = 600


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


def progress_color(remaining: float) -> str:
    return "#45d483" if remaining >= 70 else "#4da3ff" if remaining >= 30 else "#f2b84b" if remaining >= 10 else "#ef6b73"


class Progress3D:
    """High-resolution glass/metal HUD renderer with a Tkinter image target."""

    def __init__(self, canvas: tk.Canvas | None, size: int = WIDGET_SIZE):
        self.canvas = canvas
        self.size = size
        self.progress = 0.0
        self.status = "读取中…"
        self.reset_text = ""
        self.color = progress_color(0)
        self._photo = None
        self._item = None
        if canvas is not None:
            self._item = canvas.create_image(size // 2, size // 2, anchor="center")

    @staticmethod
    def clamp_progress(progress: float) -> float:
        return max(0.0, min(100.0, float(progress)))

    @staticmethod
    def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        candidates = [
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "msyhbd.ttc" if bold else "msyh.ttc"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "segoeuib.ttf" if bold else "segoeui.ttf"),
            "/System/Library/Fonts/SFNS.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for path in candidates:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def set_state(self, progress: float, status: str, reset_text: str, color: str | None = None) -> None:
        self.progress = self.clamp_progress(progress)
        self.status = status
        self.reset_text = reset_text
        self.color = color or progress_color(self.progress)
        self.render()

    def animate_to(self, progress: float, status: str, reset_text: str, color: str | None = None, done=None) -> None:
        target = self.clamp_progress(progress)
        start = self.progress
        started = time.monotonic()
        accent = color or progress_color(target)

        def step() -> None:
            ratio = min(1.0, (time.monotonic() - started) * 1000 / ANIMATION_MS)
            eased = 1 - (1 - ratio) ** 3
            self.set_state(start + (target - start) * eased, status, reset_text, accent)
            if ratio < 1.0 and self.canvas is not None:
                self.canvas.after(16, step)
            elif done:
                done()

        step()

    def render(self) -> None:
        scale = RENDER_SCALE
        size = self.size * scale
        center = size // 2
        outer = int(self.size * 0.44 * scale)
        ring_outer = int(self.size * 0.375 * scale)
        ring_inner = int(self.size * 0.305 * scale)
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        def box(radius: int) -> tuple[int, int, int, int]:
            return center - radius, center - radius, center + radius, center + radius

        shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.ellipse(box(outer + 6 * scale), fill=(0, 0, 0, 190))
        image = Image.alpha_composite(image, shadow.filter(ImageFilter.GaussianBlur(12 * scale)))
        draw = ImageDraw.Draw(image)

        draw.ellipse(box(outer), fill=(5, 12, 24, 255), outline=(126, 169, 207, 220), width=2 * scale)
        draw.ellipse(box(outer - 5 * scale), outline=(31, 75, 112, 255), width=3 * scale)
        draw.arc(box(outer - 2 * scale), 200, 320, fill=(153, 219, 255, 255), width=2 * scale)
        draw.arc(box(outer - 2 * scale), 325, 70, fill=(56, 236, 174, 190), width=2 * scale)
        draw.arc(box(outer - 2 * scale), 80, 170, fill=(135, 91, 255, 150), width=2 * scale)
        draw.ellipse(box(outer - 12 * scale), fill=(7, 15, 25, 245), outline=(15, 43, 62, 255), width=2 * scale)
        draw.ellipse(box(outer - 17 * scale), fill=(9, 20, 31, 245), outline=(29, 61, 77, 255), width=1 * scale)

        glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        arc_box = box(ring_outer)
        glow_draw.arc(arc_box, -90, 270, fill=(32, 43, 54, 235), width=13 * scale)
        glow_draw.arc(arc_box, -90, -90 + 3.6 * self.progress, fill=(*ImageColor.getrgb(self.color), 255), width=13 * scale)
        image = Image.alpha_composite(image, glow.filter(ImageFilter.GaussianBlur(9 * scale)))
        draw = ImageDraw.Draw(image)
        draw.arc(arc_box, -90, 270, fill=(32, 43, 54, 255), width=9 * scale)
        if self.progress > 0:
            draw.arc(arc_box, -90, -90 + 3.6 * self.progress, fill=ImageColor.getrgb(self.color), width=9 * scale)
        draw.ellipse(box(ring_inner), fill=(6, 14, 24, 245), outline=(19, 48, 67, 255), width=2 * scale)
        draw.arc(box(ring_inner + 2 * scale), 195, 310, fill=(79, 143, 178, 110), width=2 * scale)

        percent = f"{round(self.progress)}%" if self.status != "读取中…" or self.progress else "--"
        number_font = self._font(39 * scale, True)
        small_font = self._font(10 * scale)
        tiny_font = self._font(8 * scale)
        number_position = (center, center - 11 * scale)
        draw.text((number_position[0] + 2 * scale, number_position[1] + 3 * scale), percent, anchor="mm", font=number_font, fill=(0, 0, 0, 190))
        draw.text(number_position, percent, anchor="mm", font=number_font, fill=ImageColor.getrgb(self.color), stroke_width=1 * scale, stroke_fill=(99, 255, 190, 150))
        draw.text((center, center + 22 * scale), self.status, anchor="mm", font=small_font, fill=(226, 238, 250, 235))

        capsule = (center - 65 * scale, center + 34 * scale, center + 65 * scale, center + 57 * scale)
        capsule_glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        capsule_draw = ImageDraw.Draw(capsule_glow)
        capsule_draw.rounded_rectangle(capsule, radius=11 * scale, fill=(24, 108, 255, 150))
        image = Image.alpha_composite(image, capsule_glow.filter(ImageFilter.GaussianBlur(8 * scale)))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle(capsule, radius=11 * scale, fill=(16, 46, 91, 210), outline=(83, 153, 255, 230), width=1 * scale)
        draw.text((center, center + 45 * scale), self.reset_text or "重置时间未知", anchor="mm", font=tiny_font, fill=(220, 235, 255, 235))

        final_image = image.resize((self.size, self.size), Image.Resampling.LANCZOS)
        if self.canvas is not None:
            self._photo = ImageTk.PhotoImage(final_image)
            self.canvas.itemconfigure(self._item, image=self._photo)
        return final_image


class UsageWidget:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.transparent = "#05080d"
        self.root.overrideredirect(True)
        self.root.geometry(f"{WIDGET_SIZE}x{WIDGET_SIZE}+20+20")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=self.transparent)
        try:
            self.root.attributes("-transparentcolor", self.transparent)
        except tk.TclError:
            pass
        self._drag_offset = (0, 0)
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.refresh()

    def _build_ui(self):
        self.canvas = tk.Canvas(self.root, width=WIDGET_SIZE, height=WIDGET_SIZE, bg=self.transparent, highlightthickness=0)
        self.canvas.pack()
        self.renderer = Progress3D(self.canvas, WIDGET_SIZE)
        self.renderer.set_state(0, "读取中…", "")

        button_style = {
            "bg": self.transparent,
            "fg": "#aab5c5",
            "activebackground": "#263246",
            "activeforeground": "#ffffff",
            "font": ("Segoe UI", 9),
            "cursor": "hand2",
            "bd": 0,
            "highlightthickness": 0,
        }
        self.minimize = tk.Label(self.root, text="−", **button_style)
        self.minimize.place(x=154, y=1, width=12, height=14)
        close_style = {**button_style, "activebackground": "#672f3a", "font": ("Segoe UI", 10)}
        self.close = tk.Label(self.root, text="×", **close_style)
        self.close.place(x=167, y=1, width=12, height=14)
        self.minimize.bind("<Button-1>", lambda _event: self.root.iconify())
        self.close.bind("<Button-1>", lambda _event: self.root.destroy())
        self.canvas.bind("<ButtonPress-1>", self._drag_start)
        self.canvas.bind("<B1-Motion>", self._drag_move)

    def _drag_start(self, event):
        self._drag_offset = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())

    def _drag_move(self, event):
        self.root.geometry(f"+{event.x_root - self._drag_offset[0]}+{event.y_root - self._drag_offset[1]}")

    def refresh(self):
        self.renderer.set_state(self.renderer.progress, "读取中…", "")
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
        self.renderer.animate_to(
            remaining,
            f"{snapshot.plan} · {'可用' if snapshot.allowed else '受限'}",
            format_reset(reset_after),
            progress_color(remaining),
        )

    def _show_error(self, message: str):
        self.renderer.animate_to(0, "暂时无法读取", message[:16] or "请检查登录", "#ef6b73")


def main():
    root = tk.Tk()
    UsageWidget(root)
    root.mainloop()


if __name__ == "__main__":
    main()
