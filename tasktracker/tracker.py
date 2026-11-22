from collections.abc import Callable
from datetime import date
from typing import Any

from . import priority, storage

# Strategy table: each sort mode is a key function. Adding a mode = adding one entry.
SORT_KEYS: dict[str, Callable[[dict[str, Any]], Any]] = {
    "id": lambda t: t["id"],
    "priority": lambda t: priority.rank(t["priority"]),
    "due": lambda t: t["due"] or "9999-12-31",
}


def add_task(title, priority="medium", due=None, path=None):
    tasks = storage.load_tasks(path)
    task = {
        "id": len(tasks) + 1,
        "title": title,
        "priority": priority,
        "due": due,
        "done": False,
    }
    tasks.append(task)
    storage.save_tasks(tasks, path)
    return task


def complete_task(task_id, path=None):
    tasks = storage.load_tasks(path)
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            storage.save_tasks(tasks, path)
            return t
    return None


def delete_task(task_id, path=None):
    tasks = storage.load_tasks(path)
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) == len(tasks):
        return False
    storage.save_tasks(new_tasks, path)
    return True


def list_tasks(show_done=True, sort_by="id", path=None):
    tasks = storage.load_tasks(path)
    if not show_done:
        tasks = [t for t in tasks if not t["done"]]

    key = SORT_KEYS.get(sort_by, SORT_KEYS["id"])
    return sorted(tasks, key=key)


def overdue_tasks(today=None, path=None):
    today = today or date.today().isoformat()
    return [
        t for t in storage.load_tasks(path)
        if t["due"] and not t["done"] and t["due"] < today
    ]
