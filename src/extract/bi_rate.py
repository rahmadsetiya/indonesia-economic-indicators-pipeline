from pathlib import Path
import shutil
from datetime import datetime, timezone
import sys
import json
import hashlib

def calculate_sha256(file_path):
    with file_path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()

def find_duplicate(destination_directory, checksum):
    for metadata_file in destination_directory.glob("*.json"):
        try:
            metadata = json.loads(
                metadata_file.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Metadata JSON rusak: {metadata_file}"
            ) from error

        if metadata.get("sha256") != checksum:
            continue

        destination_value = metadata.get("destination_file")

        if not destination_value:
            raise ValueError(
                f"Metadata tidak memiliki destination_file: {metadata_file}"
            )

        existing_file = Path(destination_value)

        if existing_file.is_file():
            return existing_file

    return None

def extract_bi_rate(source_file, destination_directory):
    if not source_file.is_file():
        raise FileNotFoundError(f"File sumber tidak ditemukan: {source_file}")

    if source_file.suffix.lower() != ".xlsx":
        raise ValueError(f"File sumber harus berformat .xlsx: {source_file}")

    destination_directory.mkdir(parents=True, exist_ok=True)

    checksum = calculate_sha256(source_file)

    duplicate = find_duplicate(destination_directory, checksum)
    if duplicate is not None:
        return duplicate, False

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination_file = destination_directory / f"{timestamp}_{source_file.name}"

    shutil.copy(source_file, destination_file)

    metadata = {
        "source_file": str(source_file),
        "destination_file": str(destination_file),
        "extracted_at_utc": timestamp,
        "size_bytes": destination_file.stat().st_size,
        "sha256": checksum
    }

    metadata_file = destination_file.with_suffix(".json")

    metadata_file.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8"
    )

    return destination_file, True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Harap berikan path file sumber sebagai argumen.")

    source_file = Path(sys.argv[1])

    destination_directory = Path(
        "data/raw/bank_indonesia/bi_rate"
    )

    result, created = extract_bi_rate(source_file, destination_directory)

    if created:
        print(f"File berhasil disalin ke: {result}")
    else:
        print(f"File duplikat ditemukan, tidak disalin. File yang ada: {result}")