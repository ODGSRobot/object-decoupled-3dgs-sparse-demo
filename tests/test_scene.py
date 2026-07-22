import unittest

import numpy as np

from odgs_sparse_demo.scene import (
    HingeModel,
    RandomizationRanges,
    hinge_transform,
    sample_scene_state,
)


class SceneTest(unittest.TestCase):
    def test_hinge_center_is_fixed_by_transform(self) -> None:
        model = HingeModel(
            axis=(0.0, 0.0, 1.0),
            center_m=(0.3, -0.2, 0.1),
            lower_deg=0,
            upper_deg=90,
        )
        transform = hinge_transform(model, 45.0)
        center = np.array([0.3, -0.2, 0.1, 1.0])
        np.testing.assert_allclose(transform @ center, center, atol=1e-9)

    def test_hinge_samples_respect_boundary_margin(self) -> None:
        rng = np.random.default_rng(7)
        hinge = HingeModel(
            axis=(1.0, 0.0, 0.0),
            center_m=(0.0, 0.0, 0.0),
            lower_deg=0,
            upper_deg=90,
        )
        ranges = RandomizationRanges(hinge_boundary_margin_deg=2.0)
        samples = [sample_scene_state(rng, "hinge", ranges, hinge) for _ in range(50)]
        self.assertTrue(all(2.0 <= sample.hinge_angle_deg <= 88.0 for sample in samples))

    def test_rigid_state_has_no_hinge_angle(self) -> None:
        sample = sample_scene_state(np.random.default_rng(3), "rigid")
        self.assertIsNone(sample.hinge_angle_deg)


if __name__ == "__main__":
    unittest.main()
