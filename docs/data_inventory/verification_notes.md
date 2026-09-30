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
