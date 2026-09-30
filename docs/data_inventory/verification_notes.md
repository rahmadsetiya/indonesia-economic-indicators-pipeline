# Source verification notes

Checked 30 September 2026 against official institution pages.

- Bank Indonesia's statistics landing page exposes a current indicator display, a BI-Rate decision-history table, and daily transaction exchange rates. The exchange-rate table carries currency multipliers and buy/sell values; these cannot be collapsed into one unlabeled rate.
- BPS publishes an official national year-on-year inflation table, quarterly/annual constant-price GDP by expenditure, and national employment/unemployment values. Table identifiers are recorded in the inventory.
- BPS export/import is an interactive query with HS and aggregation choices. No production connector should be implemented until its request contract and chosen analytical grain are documented.
- `VERIFIED` means that the official page, basic semantics, and displayed grain were inspected. It does **not** mean a stable machine-readable interface is known. `INGESTIBLE` requires a documented request/response contract and representative captured payload.

The inventory deliberately keeps machine-readable format and coverage blank or “to be verified” where the official page alone does not establish them.
