# ADR 0003: PostgreSQL as the serving store

Status: Accepted

## Decision

Use PostgreSQL constraints and transactional upserts for the standardized serving layer. Keep raw and staging artifacts as files.

## Consequences

Natural-key uniqueness and referential integrity are enforced centrally. Local development needs Docker or an existing PostgreSQL instance; file-only demo and validation remain available without it.
