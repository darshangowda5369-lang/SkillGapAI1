import unittest

from app.services.progress_service import calculate_roadmap_completion_percentage


class ProgressLogicTests(unittest.TestCase):
    def test_all_completed_steps_report_as_100_percent(self):
        total_steps = 3
        completed_steps = 3
        self.assertEqual(
            calculate_roadmap_completion_percentage(total_steps, completed_steps),
            100.0,
        )

    def test_partial_completion_is_capped_to_real_progress(self):
        total_steps = 3
        completed_steps = 2
        self.assertEqual(
            calculate_roadmap_completion_percentage(total_steps, completed_steps),
            66.7,
        )


if __name__ == '__main__':
    unittest.main()
