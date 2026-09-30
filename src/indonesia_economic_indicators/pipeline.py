from __future__ import annotations

import csv
from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .common.models import CanonicalObservation
from .extract.bps_webapi import BpsApiResponse, BpsWebApiClient
from .metadata.manifest import persist_raw
from .quality.checks import QualityReport, validate
from .transform.bi_policy_rate import transform_bi_policy_rate_xlsx
from .transform.bps_dynamic import BpsPeriod, parse_bps_period_inventory, transform_bps_gdp_payload
from .transform.csv_observations import transform_csv


def _write_staging(observations: list[CanonicalObservation], staging_path: Path) -> None:
    staging_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [item.name for item in fields(CanonicalObservation)]
    with staging_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(row.to_csv_row() for row in observations)


def _persist_bps_response(
    response: BpsApiResponse,
    *,
    source: dict[str, Any],
    raw_root: Path,
    retrieved_at: datetime,
):
    return persist_raw(
        response.body,
        root=raw_root,
        institution=source["institution"],
        dataset_code=source["dataset_code"],
        source_url=response.source_url,
        retrieved_at=retrieved_at,
        original_filename=response.original_filename,
        media_type=response.media_type,
        http_status=response.status,
    )


def run_local_csv(
    input_path: Path,
    *,
    source: dict[str, Any],
    raw_root: Path,
    staging_path: Path,
    retrieved_at: datetime | None = None,
) -> tuple[list[CanonicalObservation], QualityReport]:
    retrieved_at = retrieved_at or datetime.now(UTC)
    body = input_path.read_bytes()
    manifest = persist_raw(
        body,
        root=raw_root,
        institution=source["institution"],
        dataset_code=source["dataset_code"],
        source_url=source["source_url"],
        retrieved_at=retrieved_at,
        original_filename=input_path.name,
        media_type="text/csv",
    )
    observations = transform_csv(Path(manifest.raw_file_path), source=source, manifest=manifest)
    report = validate(observations)
    report.require_pass()
    _write_staging(observations, staging_path)
    return observations, report


def run_bi_policy_rate_xlsx(
    input_path: Path,
    *,
    source: dict[str, Any],
    raw_root: Path,
    staging_path: Path,
    retrieved_at: datetime | None = None,
) -> tuple[list[CanonicalObservation], QualityReport]:
    """Persist and transform an official BI policy-rate workbook."""
    retrieved_at = retrieved_at or datetime.now(UTC)
    body = input_path.read_bytes()
    manifest = persist_raw(
        body,
        root=raw_root,
        institution=source["institution"],
        dataset_code=source["dataset_code"],
        source_url=source["source_url"],
        retrieved_at=retrieved_at,
        original_filename=input_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    observations = transform_bi_policy_rate_xlsx(
        Path(manifest.raw_file_path), source=source, manifest=manifest
    )
    report = validate(observations)
    report.require_pass()
    _write_staging(observations, staging_path)
    return observations, report


def run_bps_gdp(
    *,
    source: dict[str, Any],
    api_key: str | None,
    raw_root: Path,
    staging_path: Path,
    retrieved_at: datetime | None = None,
    client: Any | None = None,
) -> tuple[list[CanonicalObservation], QualityReport]:
    """Extract and transform the verified BPS headline real-GDP series."""
    retrieved_at = retrieved_at or datetime.now(UTC)
    if client is None:
        if not api_key:
            raise ValueError("BPS_API_KEY is required")
        client = BpsWebApiClient(api_key)

    variable_id = int(source["variable_id"])
    periods: list[BpsPeriod] = []
    page = 1
    expected_pages: int | None = None
    while expected_pages is None or page <= expected_pages:
        response = client.fetch_period_page(variable_id, page)
        manifest = _persist_bps_response(
            response, source=source, raw_root=raw_root, retrieved_at=retrieved_at
        )
        page_info, page_periods = parse_bps_period_inventory(Path(manifest.raw_file_path))
        if page_info["page"] != page:
            raise ValueError("BPS period response page does not match request")
        expected_pages = page_info["pages"]
        periods.extend(page_periods)
        page += 1

    if len({item.period_id for item in periods}) != len(periods):
        raise ValueError("BPS period inventory contains duplicate period IDs")
    if len({item.year for item in periods}) != len(periods):
        raise ValueError("BPS period inventory contains duplicate years")

    observations: list[CanonicalObservation] = []
    periods.sort(key=lambda item: item.year, reverse=True)
    for offset in range(0, len(periods), 3):
        period_ids = [item.period_id for item in periods[offset : offset + 3]]
        response = client.fetch_data(variable_id, period_ids)
        manifest = _persist_bps_response(
            response, source=source, raw_root=raw_root, retrieved_at=retrieved_at
        )
        observations.extend(
            transform_bps_gdp_payload(
                Path(manifest.raw_file_path), source=source, manifest=manifest
            )
        )

    observations.sort(key=lambda row: (row.period_start, row.period_end))
    report = validate(observations)
    report.require_pass()
    _write_staging(observations, staging_path)
    return observations, report
