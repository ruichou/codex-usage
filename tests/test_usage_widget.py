import unittest
from datetime import datetime, timezone

from usage_widget import (
    Progress3D,
    format_reset,
    parse_usage,
    progress_color,
    SPHERE_BOX,
    TEXT_RENDERER,
    WIDGET_SIZE,
)


class UsageWidgetTests(unittest.TestCase):
    def test_progress3d_clamps_state_and_preserves_copy(self):
        renderer = Progress3D(None, size=116)
        renderer.set_state(125, "Plus · 可用", "6天 20小时后重置")

        self.assertEqual(renderer.progress, 100)
        self.assertEqual(renderer.status, "Plus · 可用")
        self.assertEqual(renderer.reset_text, "6天 20小时后重置")

    def test_progress_color_matches_usage_thresholds(self):
        self.assertEqual(progress_color(70), "#45d483")
        self.assertEqual(progress_color(30), "#4da3ff")
        self.assertEqual(progress_color(10), "#f2b84b")
        self.assertEqual(progress_color(9), "#ef6b73")

    def test_reset_text_has_no_capsule_surface(self):
        renderer = Progress3D(None, size=180)
        renderer.set_state(97, "Plus · 可用", "6天 20小时后重置")
        self.assertFalse(renderer.time_capsule)

    def test_renderer_clips_pixels_outside_orb(self):
        renderer = Progress3D(None, size=180)
        image = renderer.render()
        self.assertEqual(image.getpixel((0, 0))[3], 0)

    def test_text_is_rendered_on_canvas_without_widget_background(self):
        self.assertEqual(TEXT_RENDERER, "pillow")

    def test_orb_layout_has_transparent_outer_ring(self):
        self.assertEqual(WIDGET_SIZE, 180)
        self.assertEqual(SPHERE_BOX, (10, 10, 170, 170))
        self.assertGreater(SPHERE_BOX[0], 0)

    def test_parse_usage_returns_remaining_percent_and_plan(self):
        data = {
            "plan_type": "plus",
            "rate_limit": {
                "allowed": True,
                "primary_window": {
                    "used_percent": 1,
                    "reset_at": 1786165912,
                    "reset_after_seconds": 598990,
                },
            },
        }

        snapshot = parse_usage(data)

        self.assertEqual(snapshot.plan, "Plus")
        self.assertEqual(snapshot.remaining_percent, 99)
        self.assertEqual(snapshot.reset_at, datetime.fromtimestamp(1786165912, timezone.utc))

    def test_parse_usage_clamps_used_percent(self):
        data = {
            "plan_type": "pro",
            "rate_limit": {"primary_window": {"used_percent": 120}},
        }

        self.assertEqual(parse_usage(data).remaining_percent, 0)

    def test_format_reset_shows_hours_and_minutes(self):
        self.assertEqual(format_reset(3661), "1小时 1分钟后重置")


if __name__ == "__main__":
    unittest.main()
