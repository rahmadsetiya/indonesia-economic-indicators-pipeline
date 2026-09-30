from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ..common.models import CanonicalObservation


def _psycopg():
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("PostgreSQL support requires: pip install -e '.[postgres]'") from exc
    return psycopg


@dataclass(frozen=True)
class LoadSummary:
    received: int
    inserted: int
    updated: int
    unchanged: int


def initialize_schema(database_url: str, schema_path: Path) -> None:
    psycopg = _psycopg()
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(schema_path.read_text(encoding="utf-8"))


def _dimension(cursor, table: str, code_column: str, code: str, values: dict[str, str]) -> int:
    columns = [code_column, *values.keys()]
    placeholders = ", ".join(["%s"] * len(columns))
    updates = ", ".join(f"{column}=EXCLUDED.{column}" for column in values)
    query = (
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) "
        f"ON CONFLICT ({code_column}) DO UPDATE SET {updates} "
        f"RETURNING {table.removeprefix('dim_')}_id"
    )
    cursor.execute(query, [code, *values.values()])
    return cursor.fetchone()[0]


def load_observations(database_url: str, observations: Iterable[CanonicalObservation]) -> LoadSummary:
    rows = list(observations)
    inserted = updated = unchanged = 0
    psycopg = _psycopg()
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            for row in rows:
                indicator_id = _dimension(
                    cursor, "dim_indicator", "indicator_code", row.indicator_code,
                    {"indicator_name": row.indicator_name},
                )
                geography_id = _dimension(
                    cursor, "dim_geography", "geography_code", row.geography_code,
                    {"geography_name": row.geography_name, "geography_level": row.geography_level},
                )
                unit_id = _dimension(
                    cursor, "dim_unit", "unit_code", row.unit_code,
                    {"unit_name": row.unit_name},
                )
                cursor.execute(
                    """
                    INSERT INTO dim_source
                        (institution, dataset_code, dataset_name, source_url, access_method)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (institution, dataset_code) DO UPDATE SET
                        dataset_name=EXCLUDED.dataset_name,
                        source_url=EXCLUDED.source_url,
                        access_method=EXCLUDED.access_method
                    RETURNING source_id
                    """,
                    (row.institution, row.dataset_code, row.dataset_name, row.source_url, row.access_method),
                )
                source_id = cursor.fetchone()[0]
                cursor.execute(
                    """
                    INSERT INTO source_retrieval
                        (source_id, retrieved_at, raw_file_path, checksum_sha256, http_status)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (source_id, retrieved_at, checksum_sha256) DO UPDATE SET
                        raw_file_path=EXCLUDED.raw_file_path,
                        http_status=EXCLUDED.http_status
                    RETURNING retrieval_id
                    """,
                    (source_id, row.retrieved_at, row.raw_file_path, row.checksum_sha256, row.http_status),
                )
                retrieval_id = cursor.fetchone()[0]
                cursor.execute(
                    """
                    SELECT value, retrieval_id
                    FROM fact_indicator_observation
                    WHERE indicator_id=%s AND geography_id=%s AND period_start=%s AND period_end=%s
                      AND frequency=%s AND unit_id=%s AND seasonal_adjustment=%s
                      AND price_basis=%s AND source_id=%s
                    """,
                    (
                        indicator_id, geography_id, row.period_start, row.period_end, row.frequency,
                        unit_id, row.seasonal_adjustment, row.price_basis, source_id,
                    ),
                )
                existing = cursor.fetchone()
                cursor.execute(
                    """
                    INSERT INTO fact_indicator_observation
                        (indicator_id, geography_id, period_start, period_end, frequency, value,
                         unit_id, seasonal_adjustment, price_basis, source_id, retrieval_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (indicator_id, geography_id, period_start, period_end, frequency,
                                 unit_id, seasonal_adjustment, price_basis, source_id)
                    DO UPDATE SET value=EXCLUDED.value, retrieval_id=EXCLUDED.retrieval_id,
                                  updated_at=now()
                    """,
                    (
                        indicator_id, geography_id, row.period_start, row.period_end, row.frequency,
                        row.value, unit_id, row.seasonal_adjustment, row.price_basis, source_id,
                        retrieval_id,
                    ),
                )
                if existing is None:
                    inserted += 1
                elif existing[0] == row.value:
                    unchanged += 1
                else:
                    updated += 1
    return LoadSummary(len(rows), inserted, updated, unchanged)
