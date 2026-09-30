from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from .common.config import load_sources, source_by_id
from .common.models import CanonicalObservation
from .load.postgres import initialize_schema, load_observations
from .pipeline import run_local_csv
from .quality.checks import validate


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_canonical_csv(path: Path) -> list[CanonicalObservation]:
    rows: list[CanonicalObservation] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            row["period_start"] = date.fromisoformat(row["period_start"])
            row["period_end"] = date.fromisoformat(row["period_end"])
            row["retrieved_at"] = datetime.fromisoformat(row["retrieved_at"])
            row["value"] = Decimal(row["value"])
            row["http_status"] = int(row["http_status"]) if row["http_status"] not in ("", "None") else None
            rows.append(CanonicalObservation(**row))
    return rows


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Indonesia economic indicators pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inventory", help="print configured source status")
    demo = sub.add_parser("demo", help="run the synthetic local CSV pipeline")
    demo.add_argument("--database-url", help="also load PostgreSQL")
    validate_parser = sub.add_parser("validate", help="validate a canonical staging CSV")
    validate_parser.add_argument("path", type=Path)
    init = sub.add_parser("init-db", help="create PostgreSQL schema")
    init.add_argument("--database-url", required=True)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    root = _root()
    if args.command == "inventory":
        registry = load_sources(root / "config" / "sources.yaml")
        print(json.dumps(registry, indent=2))
        return
    if args.command == "init-db":
        initialize_schema(args.database_url, root / "sql" / "schema" / "001_initial.sql")
        print("PostgreSQL schema initialized")
        return
    if args.command == "validate":
        report = validate(_read_canonical_csv(args.path))
        print(json.dumps({"rows": report.row_count, "errors": report.errors, "warnings": report.warnings}))
        sys.exit(0 if report.passed else 1)

    registry = load_sources(root / "config" / "sources.yaml")
    source = source_by_id(registry, "demo_bi_inflation")
    observations, report = run_local_csv(
        root / "examples" / "bi_inflation_sample.csv",
        source=source,
        raw_root=root / "data" / "raw",
        staging_path=root / "data" / "staging" / "demo_observations.csv",
    )
    result: dict[str, object] = {
        "source": source["id"],
        "retrieved": report.row_count,
        "validated": report.row_count,
        "rejected": len(report.errors),
        "status": "PASS",
    }
    if args.database_url:
        result["load"] = load_observations(args.database_url, observations).__dict__
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
