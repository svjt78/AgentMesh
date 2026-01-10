import json
import os
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List


class DLQStore:
    def __init__(self, storage_path: str | None = None) -> None:
        base_path = os.getenv("STORAGE_PATH", "/storage")
        resolved_path = storage_path or f"{base_path}/integration/dlq/items.jsonl"
        self.storage_path = Path(resolved_path)
        self._lock = RLock()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text("")

    def add_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        item["created_at"] = item.get("created_at") or datetime.utcnow().isoformat() + "Z"
        with self._lock:
            with self.storage_path.open("a") as f:
                f.write(json.dumps(item) + "\n")
        return item

    def list_items(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        if not self.storage_path.exists():
            return items
        with self._lock:
            for line in self.storage_path.read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return items

    def get_item(self, item_id: str) -> Dict[str, Any] | None:
        for item in self.list_items():
            if item.get("item_id") == item_id:
                return item
        return None


_dlq_store: DLQStore | None = None


def get_dlq_store() -> DLQStore:
    global _dlq_store
    if _dlq_store is None:
        _dlq_store = DLQStore()
    return _dlq_store
