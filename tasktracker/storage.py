import json
import os

DEFAULT_FILE = "tasks.json"


def get_path():
    return os.environ.get("TASKS_FILE", DEFAULT_FILE)


class StorageError(Exception):
    """The tasks file exists but cannot be used. It is never overwritten in this case."""


def load_tasks(path=None):
    path = path or get_path()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise StorageError(
                f"tasks file '{path}' is corrupted (invalid JSON: {e.msg}, line {e.lineno}). "
                "Fix or move it; it was not modified."
            ) from e
    if not isinstance(data, list):
        raise StorageError(f"tasks file '{path}' is corrupted (expected a JSON list).")
    return data


def save_tasks(tasks, path=None):
    path = path or get_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
