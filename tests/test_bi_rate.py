from src.extract.bi_rate import extract_bi_rate
import pytest

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