import json
from pathlib import Path
from typing import Any


class VendorRepository:
    def __init__(self, path: Path | None = None):
        root = Path(__file__).resolve().parents[2]
        self.path = path or root / "sample_data" / "vendors.json"
        self._vendors = self._load()

    def _load(self) -> list[dict[str, Any]]:
        with self.path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def find_by_name(self, name: str | None) -> dict[str, Any] | None:
        if not name:
            return None
        normalized = name.strip().casefold()
        for vendor in self._vendors:
            if vendor["name"].casefold() == normalized:
                return vendor
        return None

