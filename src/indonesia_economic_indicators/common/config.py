from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_sources(path: Path) -> dict[str, Any]:
    """Load the source registry.

    The checked-in file uses JSON syntax, a strict subset of YAML. This avoids a
    mandatory parser dependency while preserving the requested sources.yaml name.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("sources"), list):
        raise ValueError("source registry must contain version=1 and a sources list")
    return data


def source_by_id(registry: dict[str, Any], source_id: str) -> dict[str, Any]:
    matches = [item for item in registry["sources"] if item.get("id") == source_id]
    if len(matches) != 1:
        raise KeyError(f"expected exactly one source with id={source_id!r}")
    return matches[0]
