from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class RawManifest:
    institution: str
    dataset_code: str
    source_url: str
    retrieved_at: str
    original_filename: str
    raw_file_path: str
    checksum_sha256: str
    byte_count: int
    media_type: str
    http_status: int | None


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if not slug:
        raise ValueError("path component cannot be empty")
    return slug


def persist_raw(
    body: bytes,
    *,
    root: Path,
    institution: str,
    dataset_code: str,
    source_url: str,
    retrieved_at: datetime,
    original_filename: str,
    media_type: str = "application/octet-stream",
    http_status: int | None = None,
) -> RawManifest:
    if retrieved_at.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware")
    safe_filename = Path(original_filename).name
    timestamp = retrieved_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = root / _slug(institution) / _slug(dataset_code)
    directory.mkdir(parents=True, exist_ok=True)
    raw_path = directory / f"{timestamp}_{safe_filename}"
    checksum = hashlib.sha256(body).hexdigest()

    if raw_path.exists():
        existing_checksum = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        if existing_checksum != checksum:
            raise FileExistsError(f"immutable raw path already contains different bytes: {raw_path}")
    else:
        raw_path.write_bytes(body)

    manifest = RawManifest(
        institution=institution,
        dataset_code=dataset_code,
        source_url=source_url,
        retrieved_at=retrieved_at.isoformat(),
        original_filename=safe_filename,
        raw_file_path=raw_path.as_posix(),
        checksum_sha256=checksum,
        byte_count=len(body),
        media_type=media_type,
        http_status=http_status,
    )
    manifest_path = raw_path.with_suffix(raw_path.suffix + ".manifest.json")
    serialized = json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n"
    if manifest_path.exists() and manifest_path.read_text(encoding="utf-8") != serialized:
        raise FileExistsError(f"immutable manifest already contains different metadata: {manifest_path}")
    if not manifest_path.exists():
        manifest_path.write_text(serialized, encoding="utf-8")
    return manifest
