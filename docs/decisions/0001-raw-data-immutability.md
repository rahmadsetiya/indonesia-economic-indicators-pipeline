# ADR 0001: Immutable raw snapshots

Status: Accepted

## Decision

Persist exact retrieved bytes under a timestamped path with a JSON sidecar manifest and SHA-256 checksum. Reject a different payload targeting an existing path.

## Consequences

Transformations are reproducible and auditable. Storage grows over time, so retention policy may be needed later. Raw files are excluded from Git.
