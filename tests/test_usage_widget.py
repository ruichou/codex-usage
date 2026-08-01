import unittest
from datetime import datetime, timezone

from usage_widget import parse_usage, format_reset


class UsageWidgetTests(unittest.TestCase):
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
