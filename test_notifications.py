import os
import unittest
from unittest.mock import MagicMock, patch

import notifications


class NotificationTests(unittest.TestCase):
    def test_notify_falls_back_to_github_issue_when_slack_missing(self):
        env = {
            "GITHUB_REPOSITORY": "bdaviesweb/mlb-weather-bot",
            "GITHUB_TOKEN": "token",
        }
        list_result = MagicMock(returncode=0, stdout="", stderr="")
        create_result = MagicMock(returncode=0, stdout="https://github.com/issue/1", stderr="")

        with patch.dict(os.environ, env, clear=True), \
                patch.object(notifications, "subprocess") as subprocess:
            subprocess.run.side_effect = [list_result, create_result]

            result = notifications.notify(
                "Weather report",
                {"text": "Daily weather", "blocks": []},
                webhook_url="",
                labels=["weather-alert"],
            )

        self.assertEqual(result, "github_issue")
        self.assertEqual(subprocess.run.call_count, 2)
        self.assertIn("issue", subprocess.run.call_args_list[1].args[0])
        self.assertIn("create", subprocess.run.call_args_list[1].args[0])

    def test_github_issue_comments_on_existing_open_issue(self):
        env = {
            "GITHUB_REPOSITORY": "bdaviesweb/mlb-weather-bot",
            "GITHUB_TOKEN": "token",
        }
        list_result = MagicMock(returncode=0, stdout="42\n", stderr="")
        comment_result = MagicMock(returncode=0, stdout="", stderr="")

        with patch.dict(os.environ, env, clear=True), \
                patch.object(notifications, "subprocess") as subprocess:
            subprocess.run.side_effect = [list_result, comment_result]

            self.assertTrue(
                notifications.post_to_github_issue(
                    "Weather report",
                    {"text": "Daily weather", "blocks": []},
                )
            )

        self.assertIn("comment", subprocess.run.call_args_list[1].args[0])
        self.assertIn("42", subprocess.run.call_args_list[1].args[0])

    def test_github_issue_retries_without_missing_labels(self):
        env = {
            "GITHUB_REPOSITORY": "bdaviesweb/mlb-weather-bot",
            "GITHUB_TOKEN": "token",
        }
        list_result = MagicMock(returncode=0, stdout="", stderr="")
        create_with_labels = MagicMock(returncode=1, stdout="", stderr="could not add label")
        create_without_labels = MagicMock(returncode=0, stdout="https://github.com/issue/1", stderr="")

        with patch.dict(os.environ, env, clear=True), \
                patch.object(notifications, "subprocess") as subprocess:
            subprocess.run.side_effect = [list_result, create_with_labels, create_without_labels]

            self.assertTrue(
                notifications.post_to_github_issue(
                    "Weather report",
                    {"text": "Daily weather", "blocks": []},
                    labels=["weather-alert", "high-risk"],
                )
            )

        first_create = subprocess.run.call_args_list[1].args[0]
        retry_create = subprocess.run.call_args_list[2].args[0]
        self.assertIn("--label", first_create)
        self.assertNotIn("--label", retry_create)


if __name__ == "__main__":
    unittest.main()
