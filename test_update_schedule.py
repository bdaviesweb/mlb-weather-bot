import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytz

import update_schedule


class UpdateScheduleTests(unittest.TestCase):
    def test_fetches_two_api_dates_but_keeps_only_next_24_hours(self):
        base_now = pytz.timezone("America/Los_Angeles").localize(
            datetime(2026, 7, 17, 8, 0)
        )

        def response_for(url, timeout):
            if "date=2026-07-17" in url:
                games = [
                    self._game(
                        game_pk=1,
                        game_date="2026-07-17T18:00:00Z",
                        venue="Fenway Park",
                    )
                ]
            elif "date=2026-07-18" in url:
                games = [
                    self._game(
                        game_pk=2,
                        game_date="2026-07-18T14:30:00Z",
                        venue="Wrigley Field",
                    ),
                    self._game(
                        game_pk=3,
                        game_date="2026-07-18T17:00:00Z",
                        venue="Wrigley Field",
                    ),
                ]
            else:
                games = []

            response = MagicMock()
            response.json.return_value = {"dates": [{"games": games}]}
            return response

        with patch.object(update_schedule.requests, "get", side_effect=response_for) as get:
            games = update_schedule.get_mlb_schedule(now=base_now)

        fetched_urls = [call.args[0] for call in get.call_args_list]
        self.assertTrue(any("date=2026-07-17" in url for url in fetched_urls))
        self.assertTrue(any("date=2026-07-18" in url for url in fetched_urls))
        self.assertEqual([game["game_pk"] for game in games], [1, 2])

    def _game(self, game_pk, game_date, venue):
        return {
            "gamePk": game_pk,
            "gameDate": game_date,
            "venue": {"name": venue},
            "teams": {
                "away": {"team": {"name": "Away"}},
                "home": {"team": {"name": "Home"}},
            },
        }


if __name__ == "__main__":
    unittest.main()
