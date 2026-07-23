import unittest

import numpy as np

from odgs_sparse_demo.metrics import action_smoothness


class MetricsTest(unittest.TestCase):
    def test_action_smoothness_is_mean_squared_second_difference(self) -> None:
        actions = np.asarray([[0.0, 0.0], [1.0, 2.0], [3.0, 6.0], [6.0, 12.0]])
        second_difference = np.asarray([[1.0, 2.0], [1.0, 2.0]])
        expected = float(np.mean(np.sum(second_difference**2, axis=1)))
        self.assertEqual(action_smoothness(actions), expected)

    def test_short_sequence_has_zero_smoothness(self) -> None:
        self.assertEqual(action_smoothness([[0.0], [1.0]]), 0.0)


if __name__ == "__main__":
    unittest.main()
