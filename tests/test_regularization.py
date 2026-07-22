import unittest

import numpy as np

from odgs_sparse_demo.regularization import compose_training_loss, sequence_regularization_numpy


class RegularizationTest(unittest.TestCase):
    def test_linear_clean_trajectory_has_zero_temporal_curvature(self) -> None:
        clean = np.arange(5, dtype=float).reshape(1, 5, 1)
        velocity = np.ones_like(clean)
        time = np.array([0.5])
        noisy = clean - (1.0 - time[:, None, None]) * velocity
        mask = np.ones_like(clean)
        terms = sequence_regularization_numpy(velocity, noisy, time, mask)
        self.assertAlmostEqual(terms.temporal_consistency, 0.0)
        self.assertAlmostEqual(terms.velocity_smoothness, 0.0)

    def test_mask_excludes_invalid_action_dimensions(self) -> None:
        velocity = np.zeros((1, 3, 2), dtype=float)
        velocity[0, :, 1] = [0.0, 10.0, 0.0]
        mask = np.ones_like(velocity)
        mask[:, :, 1] = 0.0
        terms = sequence_regularization_numpy(velocity, np.zeros_like(velocity), [0.5], mask)
        self.assertEqual(terms.velocity_smoothness, 0.0)

    def test_total_loss_uses_both_weights(self) -> None:
        velocity = np.array([[[0.0], [1.0], [3.0]]])
        terms = sequence_regularization_numpy(
            velocity,
            np.zeros_like(velocity),
            np.array([0.0]),
            np.ones_like(velocity),
        )
        total = compose_training_loss(2.0, terms, temporal_weight=0.05, velocity_weight=0.02)
        expected = 2.0 + 0.05 * terms.temporal_consistency + 0.02 * terms.velocity_smoothness
        self.assertAlmostEqual(total, expected)


if __name__ == "__main__":
    unittest.main()
