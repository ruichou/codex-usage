import unittest
from datetime import datetime, timezone

from usage_widget import parse_usage, format_reset, WIDGET_SIZE, SPHERE_BOX, TEXT_LABEL_STYLE


class UsageWidgetTests(unittest.TestCase):
    def test_text_labels_have_no_frame_or_highlight(self):
        self.assertEqual(TEXT_LABEL_STYLE["bd"], 0)
        self.assertEqual(TEXT_LABEL_STYLE["highlightthickness"], 0)
        self.assertEqual(TEXT_LABEL_STYLE["relief"], "flat")

    def test_orb_layout_has_transparent_outer_ring(self):
        self.assertEqual(WIDGET_SIZE, 116)
        self.assertEqual(SPHERE_BOX, (10, 10, 106, 106))
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
