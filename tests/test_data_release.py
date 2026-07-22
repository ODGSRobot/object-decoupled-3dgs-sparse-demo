import unittest
from pathlib import Path

from odgs_sparse_demo.schemas import validate_directory


class DataReleaseTest(unittest.TestCase):
    def test_paper_facing_csv_release_is_consistent(self) -> None:
        data_dir = Path(__file__).resolve().parents[1] / "examples" / "real_data"
        self.assertEqual(validate_directory(data_dir), {})


if __name__ == "__main__":
    unittest.main()
