$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $repositoryRoot 'src'
python -m indonesia_economic_indicators.cli demo
