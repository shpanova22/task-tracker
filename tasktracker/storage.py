import json
import os

DEFAULT_FILE = "tasks.json"


def get_path():
    return os.environ.get("TASKS_FILE", DEFAULT_FILE)


def load_tasks(path=None):
    path = path or get_path()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tasks(tasks, path=None):
    path = path or get_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
