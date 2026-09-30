from __future__ import annotations

import csv
from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .common.models import CanonicalObservation
from .metadata.manifest import persist_raw
from .quality.checks import QualityReport, validate
from .transform.bi_policy_rate import transform_bi_policy_rate_xlsx
from .transform.csv_observations import transform_csv


def _write_staging(observations: list[CanonicalObservation], staging_path: Path) -> None:
    staging_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [item.name for item in fields(CanonicalObservation)]
    with staging_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(row.to_csv_row() for row in observations)


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
