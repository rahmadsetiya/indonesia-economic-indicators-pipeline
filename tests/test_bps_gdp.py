import json
import tempfile
import unittest
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from indonesia_economic_indicators.common.config import load_sources, source_by_id
from indonesia_economic_indicators.extract.bps_webapi import (
    BpsApiError,
    BpsApiResponse,
    BpsWebApiClient,
)
from indonesia_economic_indicators.pipeline import run_bps_gdp

ROOT = Path(__file__).resolve().parents[1]
YEAR_BY_PERIOD = {123: 2023, 124: 2024, 125: 2025, 126: 2026}


def _response(payload: dict[str, object], name: str, source_url: str) -> BpsApiResponse:
    return BpsApiResponse(
        body=json.dumps(payload).encode(),
        status=200,
        media_type="application/json",
        source_url=source_url,
        original_filename=name,
    )


def _period_response() -> BpsApiResponse:
    rows = [
        {"th_id": period_id, "th": str(year)}
        for period_id, year in sorted(YEAR_BY_PERIOD.items(), reverse=True)
    ]
    return _response(
        {
            "status": "OK",
            "data-availability": "available",
            "data": [
                {"page": 1, "pages": 1, "per_page": 10, "count": 4, "total": 4},
                rows,
            ],
        },
        "periods.json",
        "https://webapi.bps.go.id/v1/api/list/model/th/domain/0000/var/1956/page/1",
    )


def _data_response(period_ids: list[int]) -> BpsApiResponse:
    content: dict[str, float] = {}
    for period_id in period_ids:
        content[f"80019560{period_id}31"] = float(period_id)
        content[f"80019560{period_id}35"] = float(period_id * 4)
    return _response(
        {
            "status": "OK",
            "data-availability": "available",
            "var": [
                {
                    "val": 1956,
                    "label": "[Seri 2010] 2. PDB Triwulanan ADHK menurut Pengeluaran",
                    "unit": "Milyar Rupiah",
                    "subj": "Produk Domestik Bruto (Pengeluaran)",
                    "decimal": 2,
                }
            ],
            "turvar": [{"val": 0, "label": "Tidak ada"}],
            "vervar": [{"val": 800, "label": "8. PRODUK DOMESTIK BRUTO"}],
            "tahun": [
                {"val": period_id, "label": str(YEAR_BY_PERIOD[period_id])}
                for period_id in sorted(period_ids)
            ],
            "turtahun": [
                {"val": 31, "label": "Triwulan I"},
                {"val": 32, "label": "Triwulan II"},
                {"val": 33, "label": "Triwulan III"},
                {"val": 34, "label": "Triwulan IV"},
                {"val": 35, "label": "Tahunan"},
            ],
            "datacontent": content,
        },
        f"data_{min(period_ids)}_{max(period_ids)}.json",
        "https://webapi.bps.go.id/v1/api/list/model/data/domain/0000/var/1956",
    )


class FakeClient:
    def __init__(self) -> None:
        self.batches: list[list[int]] = []

    def fetch_period_page(self, variable_id: int, page: int) -> BpsApiResponse:
        if variable_id != 1956 or page != 1:
            raise AssertionError("unexpected period request")
        return _period_response()

    def fetch_data(self, variable_id: int, period_ids: list[int]) -> BpsApiResponse:
        if variable_id != 1956:
            raise AssertionError("unexpected variable")
        self.batches.append(period_ids)
        return _data_response(period_ids)


class BpsGdpTests(unittest.TestCase):
    def test_pipeline_batches_periods_and_transforms_headline_gdp(self):
        source = source_by_id(load_sources(ROOT / "config" / "sources.yaml"), "bps_gdp")
        client = FakeClient()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            rows, report = run_bps_gdp(
                source=source,
                api_key=None,
                raw_root=base / "raw",
                staging_path=base / "staging.csv",
                retrieved_at=datetime(2026, 9, 30, tzinfo=UTC),
                client=client,
            )

            self.assertTrue(report.passed)
            self.assertEqual(client.batches, [[126, 125, 124], [123]])
            self.assertEqual(len(rows), 8)
            self.assertEqual({row.frequency for row in rows}, {"quarterly", "annual"})
            self.assertEqual({row.price_basis for row in rows}, {"constant_2010"})
            self.assertEqual(rows[-1].value, Decimal("504.0"))
            self.assertTrue((base / "staging.csv").exists())
            self.assertEqual(len(list((base / "raw").rglob("*.manifest.json"))), 3)

    def test_network_error_does_not_disclose_api_key(self):
        secret = "a" * 32
        client = BpsWebApiClient(secret)
        with patch(
            "indonesia_economic_indicators.extract.bps_webapi.urlopen",
            side_effect=URLError("blocked"),
        ), self.assertRaises(BpsApiError) as caught:
            client.fetch_period_page(1956, 1)
        self.assertNotIn(secret, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
