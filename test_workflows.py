from pathlib import Path
import unittest


STATE_WORKFLOWS = [
    Path(".github/workflows/weather-update-v2.yml"),
    Path(".github/workflows/high-risk-alert-v2.yml"),
    Path(".github/workflows/mlb-status-monitor-v2.yml"),
]


class WorkflowNoiseTests(unittest.TestCase):
    def test_skipped_runs_do_not_commit_analytics(self):
        for workflow in STATE_WORKFLOWS:
            with self.subTest(workflow=str(workflow)):
                text = workflow.read_text()

                self.assertIn("log_workflow_run('skipped')", text)
                self.assertNotIn("Commit analytics for skipped run", text)
                self.assertNotIn("Update analytics (skipped run)", text)

    def test_actionlint_workflow_exists(self):
        workflow = Path(".github/workflows/actionlint.yml")
        text = workflow.read_text()

        self.assertIn("raven-actions/actionlint@v2", text)
        self.assertIn("pull_request", text)
        self.assertIn("workflow_dispatch", text)

    def test_no_nested_workflow_directory(self):
        self.assertFalse(Path(".github/workflows/.github").exists())

    def test_python_ci_workflow_runs_unit_tests_and_compile_check(self):
        workflow = Path(".github/workflows/python-ci.yml")
        text = workflow.read_text()

        self.assertIn("python-version: '3.10'", text)
        self.assertIn('- "*.py"', text)
        self.assertIn('- "**/*.py"', text)
        self.assertIn("pip install -r requirements.txt", text)
        self.assertIn("python -m unittest discover -p 'test_*.py'", text)
        self.assertIn("python -m py_compile", text)
        self.assertIn("test_slack_webhooks.py", text)
        self.assertIn("test_update_schedule.py", text)
        self.assertIn("test_notifications.py", text)

    def test_daily_weather_marker_only_runs_after_bot_success(self):
        text = Path(".github/workflows/weather-update-v2.yml").read_text()

        self.assertIn("id: run_weather_bot", text)
        self.assertIn("steps.run_weather_bot.outcome == 'success'", text)

    def test_high_risk_marker_only_runs_after_alert_success(self):
        text = Path(".github/workflows/high-risk-alert-v2.yml").read_text()

        self.assertIn("id: send_high_risk_alert", text)
        self.assertIn("steps.send_high_risk_alert.outcome == 'success'", text)

    def test_alert_workflows_grant_issue_fallback_permissions(self):
        for workflow in [
            Path(".github/workflows/weather-update-v2.yml"),
            Path(".github/workflows/high-risk-alert-v2.yml"),
            Path(".github/workflows/mlb-status-monitor-v2.yml"),
        ]:
            text = workflow.read_text()
            with self.subTest(workflow=str(workflow)):
                self.assertIn("issues: write", text)
                self.assertIn("GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}", text)


if __name__ == "__main__":
    unittest.main()
