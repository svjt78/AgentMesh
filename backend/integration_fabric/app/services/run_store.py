import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List


class RunStore:
    def __init__(self, storage_root: str | None = None) -> None:
        base_path = os.getenv("STORAGE_PATH", "/storage")
        resolved_path = storage_root or f"{base_path}/integration/runs"
        self.storage_root = Path(resolved_path)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    def _run_dir(self, run_id: str) -> Path:
        return self.storage_root / run_id

    def create_run(self, run_id: str, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        run_dir = self._run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "status": "running",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "completed_at": None,
            "input_data": input_data,
            "steps": [],
            "warnings": [],
            "errors": [],
        }
        with self._lock:
            (run_dir / "run.json").write_text(json.dumps(payload, indent=2))
            (run_dir / "events.jsonl").write_text("")
        return payload

    def append_event(self, run_id: str, event: Dict[str, Any]) -> None:
        run_dir = self._run_dir(run_id)
        with self._lock:
            with (run_dir / "events.jsonl").open("a") as f:
                f.write(json.dumps(event) + "\n")

    def update_run(self, run_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        run_dir = self._run_dir(run_id)
        run_file = run_dir / "run.json"
        with self._lock:
            payload = json.loads(run_file.read_text())
            payload.update(updates)
            run_file.write_text(json.dumps(payload, indent=2))
        return payload

    def append_step(self, run_id: str, step_result: Dict[str, Any]) -> None:
        run_dir = self._run_dir(run_id)
        run_file = run_dir / "run.json"
        with self._lock:
            payload = json.loads(run_file.read_text())
            payload.setdefault("steps", []).append(step_result)
            run_file.write_text(json.dumps(payload, indent=2))

    def list_runs(self) -> List[Dict[str, Any]]:
        runs: List[Dict[str, Any]] = []
        for run_dir in self.storage_root.glob("*"):
            run_file = run_dir / "run.json"
            if not run_file.exists():
                continue
            try:
                runs.append(json.loads(run_file.read_text()))
            except json.JSONDecodeError:
                continue
        runs.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return runs

    def get_run(self, run_id: str) -> Dict[str, Any]:
        run_dir = self._run_dir(run_id)
        run_file = run_dir / "run.json"
        payload = json.loads(run_file.read_text())
        events_file = run_dir / "events.jsonl"
        events: List[Dict[str, Any]] = []
        if events_file.exists():
            for line in events_file.read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        payload["events"] = events
        return payload

    def delete_run(self, run_id: str) -> None:
        run_dir = self._run_dir(run_id)
        if not run_dir.exists():
            raise FileNotFoundError(run_id)
        with self._lock:
            if run_dir.exists():
                shutil.rmtree(run_dir)


_run_store: RunStore | None = None


def get_run_store() -> RunStore:
    global _run_store
    if _run_store is None:
        _run_store = RunStore()
    return _run_store
