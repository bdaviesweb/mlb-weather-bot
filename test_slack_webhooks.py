import unittest
from unittest.mock import patch

import high_risk_alert
import mlb_game_status_monitor
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

    def test_status_monitor_alert_skips_when_webhook_missing(self):
        game_status = {
            "matchup": "Away vs Home",
            "detailed_state": "Delayed: Rain",
            "reason": "Rain",
            "away_team": "Away",
            "home_team": "Home",
            "away_score": 0,
            "home_score": 0,
            "inning": None,
            "inning_state": "",
            "venue": {
                "name": "Wrigley Field",
                "roof_type": "open_air",
                "roof_description": "Open Air",
            },
        }

        with patch.object(mlb_game_status_monitor, "SLACK_WEBHOOK", ""), \
                patch.object(mlb_game_status_monitor.requests, "post") as post:
            self.assertFalse(
                mlb_game_status_monitor.send_delay_alert(
                    game_status,
                    mlb_game_status_monitor.STATE_DELAYED,
                )
            )
            post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
