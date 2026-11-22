from datetime import date

from . import storage


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

    if sort_by == "priority":
        def key(t):
            if t["priority"] == "high":
                return 0
            elif t["priority"] == "medium":
                return 1
            elif t["priority"] == "low":
                return 2
            else:
                return 3
        tasks = sorted(tasks, key=key)
    elif sort_by == "due":
        tasks = sorted(tasks, key=lambda t: t["due"] or "9999-12-31")
    else:
        tasks = sorted(tasks, key=lambda t: t["id"])
    return tasks


def overdue_tasks(today=None, path=None):
    today = today or date.today().isoformat()
    return [
        t for t in storage.load_tasks(path)
        if t["due"] and not t["done"] and t["due"] < today
    ]
