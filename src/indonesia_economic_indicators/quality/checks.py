from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal

from ..common.models import CanonicalObservation


@dataclass
class QualityReport:
    row_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors

    def require_pass(self) -> None:
        if self.errors:
            raise ValueError("quality validation failed:\n- " + "\n- ".join(self.errors))


def validate(observations: Iterable[CanonicalObservation]) -> QualityReport:
    rows = list(observations)
    report = QualityReport(row_count=len(rows))
    seen: dict[tuple[object, ...], int] = {}
    allowed_frequencies = {"daily", "monthly", "quarterly", "semiannual", "annual", "event"}
    nonnegative_indicators = {"gdp", "export", "import"}

    if not rows:
        report.errors.append("batch contains no observations")
        return report

    for index, row in enumerate(rows, start=1):
        if row.period_end < row.period_start:
            report.errors.append(f"row {index}: period_end precedes period_start")
        if row.frequency not in allowed_frequencies:
            report.errors.append(f"row {index}: unsupported frequency {row.frequency!r}")
        if not row.indicator_code or not row.geography_code or not row.unit_code:
            report.errors.append(f"row {index}: indicator, geography, and unit are required")
        if row.indicator_code == "exchange_rate" and row.value <= Decimal(0):
            report.errors.append(f"row {index}: exchange rate must be positive")
        if row.indicator_code in nonnegative_indicators and row.value < Decimal(0):
            report.errors.append(f"row {index}: {row.indicator_code} must be nonnegative")
        if len(row.checksum_sha256) != 64:
            report.errors.append(f"row {index}: invalid SHA-256 provenance checksum")
        previous = seen.get(row.natural_key())
        if previous is not None:
            report.errors.append(f"row {index}: duplicate natural key also present at row {previous}")
        else:
            seen[row.natural_key()] = index
    return report
