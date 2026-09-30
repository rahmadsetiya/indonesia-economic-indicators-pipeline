# ADR 0002: Narrow canonical observation model

Status: Accepted for MVP

## Decision

Use a narrow fact table with dimensions for indicator, geography, unit, and source dataset. Preserve optional seasonal-adjustment and price-basis qualifiers and retain retrieval-level provenance.

## Consequences

Many indicators can share one queryable structure, while semantically distinct source series remain separate. Future source-specific dimensions may require migrations rather than overloaded columns.
