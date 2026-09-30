# Architecture overview

The MVP is a batch pipeline with four explicit boundaries:

1. **Extract** obtains bytes and response metadata. It does not reshape values.
2. **Persist raw** writes the bytes once and a sidecar manifest containing retrieval time, URL, HTTP status, media type, size, and SHA-256 checksum.
3. **Transform and validate** maps a source-specific schema to `CanonicalObservation` and runs explicit quality checks.
4. **Load** upserts dimensions, retrieval provenance, and facts inside one PostgreSQL transaction.

The raw path convention is `data/raw/<institution>/<dataset>/<UTC timestamp>_<filename>`. A conflicting write is rejected. A standardized CSV is an inspectable interchange artifact, not the source of truth for provenance.

## Canonical semantics

The core fact stores an indicator, geography, period start/end, frequency, decimal value, unit, optional seasonal adjustment and price basis, plus a source retrieval. Optional attributes remain nullable rather than being populated with misleading defaults.

The logical natural key includes source dataset because two institutions may publish similarly named but non-equivalent series. Cross-source comparison is therefore analysis, never deduplication.

## Failure behavior

- HTTP failures raise before raw persistence and include the source URL.
- Raw conflicts fail closed.
- Any validation error prevents loading the batch.
- Database loading is transactional.
- Re-running unchanged observations updates only when stored values/provenance changed.

## Deliberate omissions

Airflow, Spark, Kafka, Kubernetes, and cloud services are not needed for the current batch scale. Production scheduling, secret management, and dataset-specific BI/BPS connectors follow only after source contracts are verified.
