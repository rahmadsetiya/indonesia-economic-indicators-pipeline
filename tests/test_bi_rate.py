from src.extract.bi_rate import extract_bi_rate
import pytest
import json

def test_extract_new_file(tmp_path):
    source_file = tmp_path / "source.xlsx"
    source_file.write_bytes(b"contoh isi excel")

    destination_directory = tmp_path / "raw"

    result, created = extract_bi_rate(
        source_file,
        destination_directory,
    )

    assert created is True
    assert result.exists()
    assert result.read_bytes() == source_file.read_bytes()
    assert result.with_suffix(".json").exists()

def test_missing_source_raises_error(tmp_path):
    source_file = tmp_path / "tidak_ada.xlsx"
    destination_directory = tmp_path / "raw"

    with pytest.raises(FileNotFoundError):
        extract_bi_rate(
            source_file,
            destination_directory,
        )

def test_rejects_non_xlsx_file(tmp_path):
    source_file = tmp_path / "source.csv"
    source_file.write_text(
        "contoh,data",
        encoding="utf-8",
    )

    destination_directory = tmp_path / "raw"

    with pytest.raises(ValueError):
        extract_bi_rate(
            source_file,
            destination_directory,
        )

def test_duplicate_is_not_copied_again(tmp_path):
    source_file = tmp_path/"source.xlsx"
    source_file.write_bytes(b"contoh isi excel")

    destination_directory = tmp_path / "raw"

    first_result, first_created = extract_bi_rate(
        source_file,
        destination_directory,
    )

    second_result, second_created = extract_bi_rate(
        source_file,
        destination_directory,
    )

    assert first_created is True
    assert second_created is False
    assert second_result == first_result
    assert len(list(destination_directory.glob("*.xlsx"))) == 1
    assert len(list(destination_directory.glob("*.json"))) == 1

def test_metadata_contains_file_information(tmp_path):
    source_file = tmp_path / "source.xlsx"
    source_file.write_bytes(b"contoh isi excel")

    destination_directory = tmp_path / "raw"

    result, created = extract_bi_rate(
        source_file,
        destination_directory,
    )

    metadata_file = result.with_suffix(".json")
    metadata = json.loads(
        metadata_file.read_text(encoding="utf-8")
    )

    assert created is True
    assert metadata["source_file"] == str(source_file)
    assert metadata["destination_file"] == str(result)
    assert metadata["size_bytes"] == source_file.stat().st_size
    assert len(metadata["sha256"]) == 64
    assert metadata["extracted_at_utc"].endswith("Z")