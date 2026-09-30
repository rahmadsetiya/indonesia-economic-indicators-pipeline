# ADR 0005: Load headline real GDP from BPS variable 1956

Status: Accepted

## Context

BPS WebAPI variable `1956` contains quarterly GDP at 2010 constant prices by expenditure. Its
vertical-variable dimension includes 31 expenditure components plus code `800`, labelled
`8. PRODUK DOMESTIK BRUTO`. The payload exposes quarterly derived-period IDs `31`–`34` and annual
ID `35`. BPS limits one dynamic-data request to at most three years.

Evidence was captured from the official JSON API on 30 September 2026. The public contract is
documented at <https://webapi.bps.go.id/documentation/>.

## Decision

The first BPS production connector loads only vertical-variable code `800` as national headline
`gdp`, with `price_basis=constant_2010` and unit `billion_idr`. Quarterly and annual observations
remain distinct canonical rows. Extraction batches at most three BPS period IDs per request.

## Consequences

The connector does not silently mix GDP components with the headline series. Complete source
payloads remain immutable in raw storage, so expenditure components can be added later with an
explicit qualifier model. BPS provisional-value notes remain in raw metadata and are documented;
the current canonical schema does not claim finality.
