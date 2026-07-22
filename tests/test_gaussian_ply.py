import tempfile
import unittest
from pathlib import Path

import numpy as np

from odgs_sparse_demo.gaussian_ply import (
    read_gaussian_ply,
    split_hinged_gaussian_ply,
    write_gaussian_ply,
)


class GaussianPlyTest(unittest.TestCase):
    def test_split_preserves_every_gaussian_field(self) -> None:
        dtype = np.dtype(
            [("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("opacity", "<f4"), ("f_dc_0", "<f4")]
        )
        vertices = np.zeros(4, dtype=dtype)
        vertices["x"] = [-1.0, -0.1, 0.2, 1.0]
        vertices["opacity"] = [1.0, 2.0, 3.0, 4.0]
        vertices["f_dc_0"] = [5.0, 6.0, 7.0, 8.0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.ply"
            negative = root / "part_a.ply"
            positive = root / "part_b.ply"
            metadata = root / "hinge_split.json"
            write_gaussian_ply(source, vertices)
            split_hinged_gaussian_ply(
                source,
                negative,
                positive,
                plane_point=(0.0, 0.0, 0.0),
                plane_normal=(1.0, 0.0, 0.0),
                hinge_center=(0.0, 0.0, 0.0),
                hinge_axis=(0.0, 0.0, 1.0),
                metadata_path=metadata,
            )
            left = read_gaussian_ply(negative)
            right = read_gaussian_ply(positive)
            self.assertEqual(left.dtype.names, vertices.dtype.names)
            self.assertEqual(right.dtype.names, vertices.dtype.names)
            np.testing.assert_allclose(left["x"], [-1.0, -0.1])
            np.testing.assert_allclose(right["x"], [0.2, 1.0])
            self.assertTrue(metadata.exists())


if __name__ == "__main__":
    unittest.main()
