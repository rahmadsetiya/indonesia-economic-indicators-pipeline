from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class SourceMetadata:
    institution: str
    dataset_name: str
    dataset_code: str
    source_url: str
    access_method: str
    retrieved_at: datetime
    raw_file_path: str
    checksum_sha256: str
    http_status: int | None = None

    def __post_init__(self) -> None:
        if self.retrieved_at.tzinfo is None:
            raise ValueError("retrieved_at must be timezone-aware")


@dataclass(frozen=True)
class CanonicalObservation:
    indicator_code: str
    indicator_name: str
    geography_code: str
    geography_name: str
    geography_level: str
    period_start: date
    period_end: date
    frequency: str
    value: Decimal
    unit_code: str
    unit_name: str
    institution: str
    dataset_code: str
    dataset_name: str
    source_url: str
    access_method: str
    retrieved_at: datetime
    raw_file_path: str
    checksum_sha256: str
    seasonal_adjustment: str = ""
    price_basis: str = ""
    http_status: int | None = None

    def natural_key(self) -> tuple[Any, ...]:
        return (
            self.indicator_code,
            self.geography_code,
            self.period_start,
            self.period_end,
            self.frequency,
            self.unit_code,
            self.seasonal_adjustment,
            self.price_basis,
            self.institution,
            self.dataset_code,
        )

    def to_csv_row(self) -> dict[str, str]:
        values = asdict(self)
        return {
            key: (value.isoformat() if isinstance(value, (date, datetime)) else str(value))
            for key, value in values.items()
        }


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
