from __future__ import annotations

import csv
from dataclasses import fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .common.models import CanonicalObservation
from .metadata.manifest import persist_raw
from .quality.checks import QualityReport, validate
from .transform.csv_observations import transform_csv


def run_local_csv(
    input_path: Path,
    *,
    source: dict[str, Any],
    raw_root: Path,
    staging_path: Path,
    retrieved_at: datetime | None = None,
) -> tuple[list[CanonicalObservation], QualityReport]:
    retrieved_at = retrieved_at or datetime.now(timezone.utc)
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
    staging_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [item.name for item in fields(CanonicalObservation)]
    with staging_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(row.to_csv_row() for row in observations)
    return observations, report
