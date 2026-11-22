from tasktracker import tracker


def test_add_task(tmp_path):
    f = tmp_path / "tasks.json"
    t = tracker.add_task("Buy milk", path=str(f))
    assert t["id"] == 1
    assert t["done"] is False
    assert len(tracker.list_tasks(path=str(f))) == 1


def test_complete_task(tmp_path):
    f = str(tmp_path / "tasks.json")
    tracker.add_task("Write report", path=f)
    t = tracker.complete_task(1, path=f)
    assert t["done"] is True


def test_complete_missing_task(tmp_path):
    f = str(tmp_path / "tasks.json")
    assert tracker.complete_task(42, path=f) is None


def test_list_pending_only(tmp_path):
    f = str(tmp_path / "tasks.json")
    tracker.add_task("A", path=f)
    tracker.add_task("B", path=f)
    tracker.complete_task(1, path=f)
    pending = tracker.list_tasks(show_done=False, path=f)
    assert [t["title"] for t in pending] == ["B"]


def test_sort_by_priority(tmp_path):
    f = str(tmp_path / "tasks.json")
    tracker.add_task("low one", priority="low", path=f)
    tracker.add_task("high one", priority="high", path=f)
    tracker.add_task("mid one", priority="medium", path=f)
    titles = [t["title"] for t in tracker.list_tasks(sort_by="priority", path=f)]
    assert titles == ["high one", "mid one", "low one"]


def test_overdue(tmp_path):
    f = str(tmp_path / "tasks.json")
    tracker.add_task("old", due="2020-01-01", path=f)
    tracker.add_task("future", due="2999-01-01", path=f)
    over = tracker.overdue_tasks(today="2026-11-22", path=f)
    assert [t["title"] for t in over] == ["old"]
