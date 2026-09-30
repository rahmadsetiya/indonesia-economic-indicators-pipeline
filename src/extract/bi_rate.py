from pathlib import Path

source_file = Path(
  "C:/Users/MyPC Pro/Downloads/BI-7Day-RR.xlsx"
)

destination_directory = Path(
  "data/raw/bank_indonesia/bi_rate"
)

destination_directory.mkdir(parents=True, exist_ok=True)

print(source_file)
print(source_file.exists())