import unittest
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal

from indonesia_economic_indicators.common.models import CanonicalObservation
from indonesia_economic_indicators.quality.checks import validate


def observation() -> CanonicalObservation:
    return CanonicalObservation(
        indicator_code="exchange_rate",
        indicator_name="Exchange rate",
        geography_code="IDN",
        geography_name="Indonesia",
        geography_level="national",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 1),
        frequency="daily",
        value=Decimal("16000"),
        unit_code="idr_per_usd",
        unit_name="IDR per USD",
        institution="Bank Indonesia",
        dataset_code="TEST",
        dataset_name="Test",
        source_url="https://example.invalid",
        access_method="fixture",
        retrieved_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        raw_file_path="raw/test.csv",
        checksum_sha256="a" * 64,
    )


class QualityTests(unittest.TestCase):
    def test_duplicate_natural_key_is_rejected(self):
        row = observation()
        report = validate([row, row])
        self.assertFalse(report.passed)
        self.assertIn("duplicate natural key", report.errors[0])

    def test_nonpositive_exchange_rate_is_rejected(self):
        report = validate([replace(observation(), value=Decimal("0"))])
        self.assertFalse(report.passed)


if __name__ == "__main__":
    unittest.main()
