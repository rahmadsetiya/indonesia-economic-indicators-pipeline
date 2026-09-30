from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ..common.models import CanonicalObservation
from ..metadata.manifest import RawManifest


@dataclass(frozen=True)
class BpsPeriod:
    period_id: int
    year: int


def _payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_bytes())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("BPS response is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise TypeError("BPS response must be a JSON object")
    if payload.get("status") != "OK":
        message = payload.get("message", "unknown application error")
        raise ValueError(f"BPS application error: {message}")
    return payload


def parse_bps_period_inventory(path: Path) -> tuple[dict[str, int], list[BpsPeriod]]:
    payload = _payload(path)
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 2:
        raise ValueError("BPS period response must contain page metadata and rows")
    page_info, raw_rows = data
    if not isinstance(page_info, dict) or not isinstance(raw_rows, list):
        raise TypeError("BPS period response has invalid pagination structure")
    required = ("page", "pages", "count", "total")
    try:
        pagination = {name: int(page_info[name]) for name in required}
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("BPS period response has invalid pagination metadata") from exc

    periods: list[BpsPeriod] = []
    for raw_row in raw_rows:
        if not isinstance(raw_row, dict):
            raise TypeError("BPS period row must be an object")
        try:
            period_id = int(raw_row["th_id"])
            year = int(raw_row["th"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid BPS period row: {raw_row!r}") from exc
        periods.append(BpsPeriod(period_id=period_id, year=year))
    if pagination["count"] != len(periods):
        raise ValueError("BPS period page count does not match returned rows")
    return pagination, periods


def _period_bounds(year: int, derived_period_id: int) -> tuple[date, date, str]:
    if derived_period_id == 31:
        return date(year, 1, 1), date(year, 3, 31), "quarterly"
    if derived_period_id == 32:
        return date(year, 4, 1), date(year, 6, 30), "quarterly"
    if derived_period_id == 33:
        return date(year, 7, 1), date(year, 9, 30), "quarterly"
    if derived_period_id == 34:
        return date(year, 10, 1), date(year, 12, 31), "quarterly"
    if derived_period_id == 35:
        return date(year, 1, 1), date(year, 12, 31), "annual"
    raise ValueError(f"unsupported BPS GDP derived period ID: {derived_period_id}")


def _decimal(value: object, key: str) -> Decimal:
    if value is None or isinstance(value, bool):
        raise ValueError(f"BPS datacontent {key!r} has invalid value {value!r}")
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"BPS datacontent {key!r} has invalid value {value!r}") from exc


def transform_bps_gdp_payload(
    path: Path,
    *,
    source: dict[str, Any],
    manifest: RawManifest,
) -> list[CanonicalObservation]:
    payload = _payload(path)
    variable_id = int(source["variable_id"])
    vertical_code = int(source["vertical_variable_code"])
    derived_variable_id = int(source.get("derived_variable_id", 0))

    variables = payload.get("var")
    if not isinstance(variables, list) or len(variables) != 1:
        raise ValueError("BPS GDP payload must describe exactly one variable")
    variable = variables[0]
    if not isinstance(variable, dict) or int(variable.get("val", -1)) != variable_id:
        raise ValueError("BPS GDP payload variable ID does not match source configuration")
    if variable.get("unit") != source["source_unit"]:
        raise ValueError("BPS GDP payload unit does not match source configuration")

    verticals = payload.get("vervar")
    if not isinstance(verticals, list):
        raise TypeError("BPS GDP payload is missing vertical-variable metadata")
    matches = [
        item
        for item in verticals
        if isinstance(item, dict) and int(item.get("val", -1)) == vertical_code
    ]
    if len(matches) != 1 or matches[0].get("label") != source["vertical_variable_label"]:
        raise ValueError("BPS GDP headline component metadata does not match configuration")

    years = payload.get("tahun")
    derived_periods = payload.get("turtahun")
    content = payload.get("datacontent")
    if not isinstance(years, list) or not isinstance(derived_periods, list):
        raise TypeError("BPS GDP payload is missing period metadata")
    if not isinstance(content, dict):
        raise TypeError("BPS GDP payload is missing datacontent")

    observations: list[CanonicalObservation] = []
    for year_item in years:
        if not isinstance(year_item, dict):
            raise TypeError("BPS GDP year metadata must be an object")
        period_id = int(year_item["val"])
        year = int(year_item["label"])
        for derived_item in derived_periods:
            if not isinstance(derived_item, dict):
                raise TypeError("BPS GDP derived-period metadata must be an object")
            derived_period_id = int(derived_item["val"])
            key = (
                f"{vertical_code}{variable_id}{derived_variable_id}"
                f"{period_id}{derived_period_id}"
            )
            if key not in content:
                continue
            period_start, period_end, frequency = _period_bounds(year, derived_period_id)
            observations.append(
                CanonicalObservation(
                    indicator_code=source["indicator_code"],
                    indicator_name=source["indicator_name"],
                    geography_code=source["geography_code"],
                    geography_name=source["geography_name"],
                    geography_level=source["geography_level"],
                    period_start=period_start,
                    period_end=period_end,
                    frequency=frequency,
                    value=_decimal(content[key], key),
                    unit_code=source["unit_code"],
                    unit_name=source["unit_name"],
                    institution=source["institution"],
                    dataset_code=source["dataset_code"],
                    dataset_name=source["dataset_name"],
                    source_url=manifest.source_url,
                    access_method=source["access_method"],
                    retrieved_at=datetime.fromisoformat(manifest.retrieved_at),
                    raw_file_path=manifest.raw_file_path,
                    checksum_sha256=manifest.checksum_sha256,
                    price_basis=source["price_basis"],
                    http_status=manifest.http_status,
                )
            )
    if not observations:
        raise ValueError("BPS GDP payload contains no headline observations")
    return sorted(observations, key=lambda row: (row.period_start, row.period_end))
