from __future__ import annotations

import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ..common.models import CanonicalObservation
from ..metadata.manifest import RawManifest


def _date(value: str, field: str, row_number: int) -> date:
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(f"row {row_number}: invalid {field} ISO date {value!r}") from exc


def transform_csv(
    path: Path,
    *,
    source: dict[str, Any],
    manifest: RawManifest,
) -> list[CanonicalObservation]:
    observations: list[CanonicalObservation] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"period_start", "period_end", "value"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing required CSV columns: {sorted(missing)}")
        for row_number, row in enumerate(reader, start=2):
            try:
                value = Decimal(row["value"].strip())
            except (InvalidOperation, AttributeError) as exc:
                raise ValueError(f"row {row_number}: invalid decimal value {row.get('value')!r}") from exc
            observations.append(
                CanonicalObservation(
                    indicator_code=source["indicator_code"],
                    indicator_name=source.get("indicator_name", source["indicator_code"]),
                    geography_code=source["geography_code"],
                    geography_name=source.get("geography_name", "Indonesia"),
                    geography_level=source.get("geography_level", "national"),
                    period_start=_date(row["period_start"], "period_start", row_number),
                    period_end=_date(row["period_end"], "period_end", row_number),
                    frequency=source["frequency"],
                    value=value,
                    unit_code=source["unit_code"],
                    unit_name=source.get("unit_name", source["unit_code"]),
                    institution=source["institution"],
                    dataset_code=source["dataset_code"],
                    dataset_name=source["dataset_name"],
                    source_url=source["source_url"],
                    access_method=source["access_method"],
                    retrieved_at=datetime.fromisoformat(manifest.retrieved_at),
                    raw_file_path=manifest.raw_file_path,
                    checksum_sha256=manifest.checksum_sha256,
                    seasonal_adjustment=row.get("seasonal_adjustment", "").strip(),
                    price_basis=row.get("price_basis", "").strip(),
                    http_status=manifest.http_status,
                )
            )
    return observations
