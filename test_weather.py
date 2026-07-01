from datetime import datetime
from contextlib import redirect_stdout
from io import StringIO
import unittest

from weather import (
    build_weather_from_period,
    calculate_game_impact,
    is_high_risk,
)


class WeatherRuleTests(unittest.TestCase):
    def test_slight_chance_thunderstorm_is_not_high_risk(self):
        period = {
            "windSpeed": "8 mph",
            "probabilityOfPrecipitation": {"value": 45},
            "temperature": 72,
            "shortForecast": "Slight Chance Showers And Thunderstorms",
            "detailedForecast": "A slight chance of showers and thunderstorms.",
            "startTime": "2026-07-01T19:00:00-05:00",
        }

        with redirect_stdout(StringIO()):
            weather = build_weather_from_period(
                location="Chicago,US",
                game_local=datetime.fromisoformat("2026-07-01T19:05:00-05:00"),
                period=period,
            )

        self.assertFalse(weather["has_thunderstorm"])
        self.assertFalse(is_high_risk(weather))
        self.assertEqual(calculate_game_impact(weather)["level"], "MONITOR")

    def test_active_thunderstorm_with_rain_is_high_risk(self):
        period = {
            "windSpeed": "12 mph",
            "probabilityOfPrecipitation": {"value": 55},
            "temperature": 78,
            "shortForecast": "Thunderstorms",
            "detailedForecast": "Thunderstorms likely near game time.",
            "startTime": "2026-07-01T19:00:00-05:00",
        }

        with redirect_stdout(StringIO()):
            weather = build_weather_from_period(
                location="Chicago,US",
                game_local=datetime.fromisoformat("2026-07-01T19:05:00-05:00"),
                period=period,
            )

        self.assertTrue(weather["has_thunderstorm"])
        self.assertTrue(is_high_risk(weather))
        self.assertIn("Active thunderstorms", weather["trigger_reason"])
        self.assertEqual(calculate_game_impact(weather)["level"], "HIGH_RISK")

    def test_wind_range_uses_highest_speed(self):
        period = {
            "windSpeed": "15 to 25 mph",
            "probabilityOfPrecipitation": {"value": None},
            "temperature": 65,
            "shortForecast": "Partly Cloudy",
            "detailedForecast": "",
            "startTime": "2026-07-01T19:00:00-05:00",
        }

        with redirect_stdout(StringIO()):
            weather = build_weather_from_period(
                location="Chicago,US",
                game_local=datetime.fromisoformat("2026-07-01T19:05:00-05:00"),
                period=period,
            )

        self.assertEqual(weather["wind_speed"], 25)
        self.assertEqual(weather["rain_prob"], 0)
        self.assertEqual(calculate_game_impact(weather)["level"], "MONITOR")


if __name__ == "__main__":
    unittest.main()
