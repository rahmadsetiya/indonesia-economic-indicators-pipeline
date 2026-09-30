# Contributing

Use a short-lived branch and keep commits focused. Before opening a pull request:

```powershell
python -m unittest discover -s tests -v
python -m indonesia_economic_indicators.cli demo
```

Connector pull requests should include an updated source-inventory row, sample fixture with no secrets, extraction/transform tests, provenance fields, expected natural key, and known limitations. Avoid broad refactors in the same commit as a new connector.
