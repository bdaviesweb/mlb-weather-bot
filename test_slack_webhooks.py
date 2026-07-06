import unittest
from unittest.mock import patch

import high_risk_alert
import weather_bot


class SlackWebhookConfigTests(unittest.TestCase):
    def test_daily_weather_post_skips_when_webhook_missing(self):
        with patch.object(weather_bot, "SLACK_WEBHOOK", ""), \
                patch.object(weather_bot.requests, "post") as post:
            self.assertFalse(weather_bot.post_to_slack({"text": "test"}))
            post.assert_not_called()

    def test_high_risk_post_skips_when_webhook_missing(self):
        with patch.object(high_risk_alert, "SLACK_WEBHOOK", ""), \
                patch.object(high_risk_alert.requests, "post") as post:
            self.assertFalse(high_risk_alert.post_to_slack({"text": "test"}))
            post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
