import tempfile
import unittest
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook

from indonesia_economic_indicators.common.config import load_sources, source_by_id
from indonesia_economic_indicators.pipeline import run_bi_policy_rate_xlsx

ROOT = Path(__file__).resolve().parents[1]


def _workbook(path: Path, *, header: str = "BI-7Day-RR") -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "BI-7Day-RR"
    sheet["A3"] = "BI-7Day-RR"
    sheet.append([])
    sheet["A5"] = "NO"
    sheet["B5"] = "Tanggal"
    sheet["C5"] = header
    sheet.append([1, "18 Juni 2026", "5.75%"])
    sheet.append([2, "17 Juni 2026", "5.50%"])
    sheet.append([3, "21 Mei 2026", "5.50%"])
    workbook.save(path)
    workbook.close()


class BiPolicyRateTests(unittest.TestCase):
    def test_official_layout_transforms_as_event_series_with_provenance(self):
        registry = load_sources(ROOT / "config" / "sources.yaml")
        source = source_by_id(registry, "bi_policy_rate")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            input_path = base / "BI-7Day-RR.xlsx"
            _workbook(input_path)
            rows, report = run_bi_policy_rate_xlsx(
                input_path,
                source=source,
                raw_root=base / "raw",
                staging_path=base / "staging.csv",
                retrieved_at=datetime(2026, 9, 30, tzinfo=UTC),
            )

            self.assertTrue(report.passed)
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0].frequency, "event")
            self.assertEqual(rows[0].period_start.isoformat(), "2026-06-18")
            self.assertEqual(rows[0].period_start, rows[0].period_end)
            self.assertEqual(rows[0].value, Decimal("5.75"))
            self.assertNotEqual(rows[0].natural_key(), rows[1].natural_key())
            self.assertTrue(Path(rows[0].raw_file_path).exists())
            self.assertTrue(Path(rows[0].raw_file_path + ".manifest.json").exists())
            self.assertTrue((base / "staging.csv").exists())

    def test_layout_change_fails_explicitly(self):
        registry = load_sources(ROOT / "config" / "sources.yaml")
        source = source_by_id(registry, "bi_policy_rate")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            input_path = base / "changed.xlsx"
            _workbook(input_path, header="Changed")
            with self.assertRaisesRegex(ValueError, "unexpected BI workbook headers"):
                run_bi_policy_rate_xlsx(
                    input_path,
                    source=source,
                    raw_root=base / "raw",
                    staging_path=base / "staging.csv",
                    retrieved_at=datetime(2026, 9, 30, tzinfo=UTC),
                )


if __name__ == "__main__":
    unittest.main()
