# ADR 0004: Model the BI policy rate as an event series

Status: Accepted

## Context

The official BI workbook records one row per policy decision date. It can contain more than one
decision in a calendar month, so a monthly key would discard information or create duplicates.
Bank Indonesia implemented the BI 7-Day (Reverse) Repo Rate on 19 August 2016 and changed its
name to BI-Rate on 21 December 2023 without changing the instrument's meaning or purpose.

Evidence:

- <https://www.bi.go.id/id/statistik/indikator/bi-rate.aspx>
- <https://www.bi.go.id/id/fungsi-utama/moneter/bi-rate/default.aspx>

## Decision

Represent each workbook row as a national `policy_rate` observation with `frequency=event` and
`period_start=period_end=decision date`. Keep one source dataset across the documented naming
change, and retain the source dataset name `BI-Rate decision history (BI7DRR / BI-Rate)` so the
historical naming regime remains visible.

## Consequences

Multiple decisions in one month remain distinct and idempotent under the canonical natural key.
Monthly analytical series must be derived explicitly later (for example, month-end effective rate)
rather than being implied during extraction. A change to this interpretation requires a migration.
