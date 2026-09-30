# Source verification notes

Checked 30 September 2026 against official institution pages.

- Bank Indonesia's statistics landing page exposes a current indicator display, a BI-Rate decision-history table, and daily transaction exchange rates. The exchange-rate table carries currency multipliers and buy/sell values; these cannot be collapsed into one unlabeled rate.
- BPS publishes an official national year-on-year inflation table, quarterly/annual constant-price GDP by expenditure, and national employment/unemployment values. Table identifiers are recorded in the inventory.
- BPS export/import is an interactive query with HS and aggregation choices. No production connector should be implemented until its request contract and chosen analytical grain are documented.
- `VERIFIED` means that the official page, basic semantics, and displayed grain were inspected. It does **not** mean a stable machine-readable interface is known. `INGESTIBLE` requires a documented request/response contract and representative captured payload.

The inventory deliberately keeps machine-readable format and coverage blank or “to be verified” where the official page alone does not establish them.

## Bank Indonesia policy-rate workbook

Checked 30 September 2026 using the download control on the official
[BI-Rate indicator page](https://www.bi.go.id/id/statistik/indikator/bi-rate.aspx).

- The downloaded workbook has one worksheet, `BI-7Day-RR`, with headers in row 5 and 128 populated
  observations in rows 6–133.
- The observed snapshot runs from 21 April 2016 through 23 September 2026. Dates are unique and
  sorted newest-to-oldest. Two months contain more than one decision, confirming an event grain.
- Date and percentage cells are strings (for example, an Indonesian date and `5.75%`). The connector
  validates this contract instead of coercing an unknown replacement layout.
- The workbook does not contain the press-release-link column displayed on the web page.
- Repeated downloads produced the same observed table and byte count but different file checksums.
  Workbook generation metadata is a plausible cause, but that causal explanation is not verified.
- The web control uses a dynamic ASP.NET postback rather than a stable public file URL. The implemented
  connector therefore starts from a user-downloaded official XLSX. Automated acquisition remains a
  separate task and must not depend on an undocumented private endpoint.

`IMPLEMENTED` means the local-XLSX extraction, raw manifest, transformation, validation, and tests
exist. Promotion to `VALIDATED` requires repeat operational runs and a verified PostgreSQL load.

## BPS WebAPI real GDP

Checked 30 September 2026 against the official authenticated JSON API and its
[public documentation](https://webapi.bps.go.id/documentation/).

- The national domain is `0000`; the verified domain inventory contained 549 BPS domains.
- Dynamic variable `1956` is `[Seri 2010] 2. PDB Triwulanan Atas Dasar Harga Konstan menurut
  Pengeluaran`, measured in `Milyar Rupiah`.
- The period inventory contained 17 years, 2010–2026. The vertical-variable inventory contained 32
  entries; code `800` is the headline `8. PRODUK DOMESTIK BRUTO` selected by this connector.
- Derived-period IDs `31`–`34` are quarters I–IV and ID `35` is annual. The connector constructs
  source keys from verified dimension IDs instead of parsing variable-length concatenated keys.
- The API rejected a 17-year request and stated a maximum of three years for `th`; extraction now
  batches no more than three years per request.
- Source metadata marks 2024 provisional, 2025 very provisional, and 2026 very-very provisional.
  Those notes remain in every raw payload and must be considered in revision analysis.
- The API can return HTTP 200 with an application-level `status=Error`; both layers are validated.
  API keys are read only from `BPS_API_KEY`, excluded from public provenance URLs, and never logged.

`IMPLEMENTED` means extraction, immutable raw payloads/manifests, headline transformation, quality
validation, CLI integration, and offline tests exist. PostgreSQL integration remains to be run before
promotion to `VALIDATED`.
