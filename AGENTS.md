# Working Agreement

This repository is both a learning project and a research artifact.

1. Preserve raw source bytes. Never edit files under `data/raw` in place.
2. Do not present an endpoint, definition, comparison, or research gap as verified without evidence.
3. Keep extraction, transformation, validation, and loading separate.
4. Prefer simple, explicit Python and SQL over additional infrastructure.
5. Each production connector needs inventory evidence, a captured representative payload, provenance, error handling, and tests.
6. A logical observation is unique by indicator, geography, period, frequency, source dataset, and relevant qualifiers.
7. Changes to canonical semantics require an ADR and migration.
8. Unit tests must not call live official services. Mark integration tests explicitly.
9. Do not commit credentials, downloaded raw data, or local `.env` files.
