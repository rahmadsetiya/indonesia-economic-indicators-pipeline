# Indonesia Economic Indicators Pipeline

A learning-focused, reproducible data-engineering project for integrating national-level Indonesian macroeconomic indicators from official sources. The pipeline keeps source bytes immutable, records provenance, standardizes observations, validates quality, and loads PostgreSQL idempotently.

> Status: foundation/MVP. The local synthetic demo is runnable. BI and BPS source records are discovery entries—not claims that production extractors are complete.

## Scope

- National indicators only: inflation, BI policy rate, rupiah exchange rate, GDP, unemployment, exports, and imports.
- Official APIs or machine-readable downloads are preferred over HTML; PDF is a last resort.
- Regional PDRB and orchestration platforms are intentionally out of scope for the MVP.

## Data flow

```text
official source -> extract -> immutable raw bytes + manifest
                -> transform -> canonical CSV -> validate
                -> PostgreSQL upsert
```

Every canonical row carries an institution, dataset code, source URL, retrieval timestamp, raw path, and checksum. The database natural key prevents duplicate logical observations.

## Quick start

Requirements: Python 3.11+; Docker is optional for PostgreSQL.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,postgres]"
python -m unittest discover -s tests -v
python -m indonesia_economic_indicators.cli demo
```

The demo uses clearly labelled synthetic observations from `examples/bi_inflation_sample.csv`. It creates an immutable raw snapshot and validated staging CSV without calling an external service.

To test PostgreSQL loading:

```powershell
Copy-Item .env.example .env
docker compose up -d db
python -m indonesia_economic_indicators.cli init-db --database-url "postgresql://indicators:indicators@localhost:5432/indicators"
python -m indonesia_economic_indicators.cli demo --database-url "postgresql://indicators:indicators@localhost:5432/indicators"
```

Run `demo` twice. The second database load must report unchanged rows rather than new logical observations.

## Commands

```text
python -m indonesia_economic_indicators.cli inventory
python -m indonesia_economic_indicators.cli demo [--database-url URL]
python -m indonesia_economic_indicators.cli validate PATH
python -m indonesia_economic_indicators.cli init-db --database-url URL
```

## Repository guide

- `config/sources.yaml`: source registry (JSON syntax, which is valid YAML, so the runtime stays dependency-light).
- `docs/data_inventory/source_inventory.csv`: discovery evidence and implementation status.
- `src/indonesia_economic_indicators/`: extraction, metadata, transformation, quality, loading, and CLI code.
- `sql/schema/001_initial.sql`: canonical PostgreSQL schema and idempotency constraints.
- `docs/decisions/`: short architecture decisions, including tradeoffs.
- `paper/notes/`: evidence-first research notes; no research gap is asserted.

## Development sequence

Before implementing a production connector, move its inventory row through `DISCOVERED -> VERIFIED -> INGESTIBLE -> IMPLEMENTED -> VALIDATED`. Capture a representative payload and identify its natural key, units, historical coverage, revision behavior, and authentication requirements. Add connector tests before moving to the next source.

See [CONTRIBUTING.md](CONTRIBUTING.md), [architecture](docs/architecture/overview.md), and [source inventory](docs/data_inventory/source_inventory.csv).
