import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from indonesia_economic_indicators.metadata.manifest import persist_raw


class ManifestTests(unittest.TestCase):
    def test_repeat_identical_write_is_safe_but_conflict_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            kwargs = {
                "root": Path(directory),
                "institution": "Bank Indonesia",
                "dataset_code": "DEMO",
                "source_url": "https://example.invalid/demo",
                "retrieved_at": datetime(2026, 1, 1, tzinfo=UTC),
                "original_filename": "data.csv",
            }
            first = persist_raw(b"same", **kwargs)
            second = persist_raw(b"same", **kwargs)
            self.assertEqual(first.checksum_sha256, second.checksum_sha256)
            with self.assertRaises(FileExistsError):
                persist_raw(b"different", **kwargs)


if __name__ == "__main__":
    unittest.main()
