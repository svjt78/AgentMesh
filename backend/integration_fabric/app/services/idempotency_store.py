import json
import os
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional


class IdempotencyStore:
    def __init__(self, storage_path: str | None = None) -> None:
        base_path = os.getenv("STORAGE_PATH", "/storage")
        resolved_path = storage_path or f"{base_path}/integration/idempotency.json"
        self.storage_path = Path(resolved_path)
        self._lock = RLock()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text("{}")

    def _load(self) -> Dict[str, Any]:
        try:
            return json.loads(self.storage_path.read_text())
        except json.JSONDecodeError:
            return {}

    def _save(self, data: Dict[str, Any]) -> None:
        self.storage_path.write_text(json.dumps(data, indent=2))

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            data = self._load()
            return data.get(key)

    def set(self, key: str, value: Dict[str, Any]) -> None:
        with self._lock:
            data = self._load()
            data[key] = value
            self._save(data)


_idempotency_store: Optional[IdempotencyStore] = None


def get_idempotency_store() -> IdempotencyStore:
    global _idempotency_store
    if _idempotency_store is None:
        _idempotency_store = IdempotencyStore()
    return _idempotency_store
