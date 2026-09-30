import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from indonesia_economic_indicators.common.config import load_sources, source_by_id
from indonesia_economic_indicators.pipeline import run_local_csv

ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_demo_transforms_and_validates(self):
        registry = load_sources(ROOT / "config" / "sources.yaml")
        source = source_by_id(registry, "demo_bi_inflation")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            rows, report = run_local_csv(
                ROOT / "examples" / "bi_inflation_sample.csv",
                source=source,
                raw_root=base / "raw",
                staging_path=base / "staging.csv",
                retrieved_at=datetime(2026, 3, 31, tzinfo=UTC),
            )
            self.assertTrue(report.passed)
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0].natural_key()[0], "inflation_yoy")
            self.assertTrue((base / "staging.csv").exists())


if __name__ == "__main__":
    unittest.main()
