import unittest

from analytics import calculate_workflow_reliability


class WorkflowReliabilityTests(unittest.TestCase):
    def test_uptime_excludes_skipped_runs(self):
        workflow_runs = {
            "total_runs": 10,
            "successful_runs": 4,
            "failed_runs": 1,
            "skipped_runs": 5,
        }

        reliability = calculate_workflow_reliability(workflow_runs)

        self.assertEqual(reliability["attempted_runs"], 5)
        self.assertEqual(reliability["success_rate"], 80.0)
        self.assertEqual(reliability["skipped_rate"], 50.0)

    def test_uptime_is_zero_when_no_attempted_runs(self):
        workflow_runs = {
            "total_runs": 3,
            "successful_runs": 0,
            "failed_runs": 0,
            "skipped_runs": 3,
        }

        reliability = calculate_workflow_reliability(workflow_runs)

        self.assertEqual(reliability["attempted_runs"], 0)
        self.assertEqual(reliability["success_rate"], 0)
        self.assertEqual(reliability["skipped_rate"], 100.0)


if __name__ == "__main__":
    unittest.main()
