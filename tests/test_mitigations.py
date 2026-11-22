import pytest

from tasktracker import cli, storage, tracker


# M1 / RISK-01: ids must stay unique after a delete
def test_ids_unique_after_delete(tmp_path):
    f = str(tmp_path / "tasks.json")
    for title in ("A", "B", "C"):
        tracker.add_task(title, path=f)
    tracker.delete_task(1, path=f)
    d = tracker.add_task("D", path=f)
    ids = [t["id"] for t in tracker.list_tasks(path=f)]
    assert d["id"] == 4
    assert len(ids) == len(set(ids))


def test_delete_after_readd_removes_only_one_task(tmp_path):
    f = str(tmp_path / "tasks.json")
    for title in ("A", "B", "C"):
        tracker.add_task(title, path=f)
    tracker.delete_task(1, path=f)
    tracker.add_task("D", path=f)
    tracker.delete_task(3, path=f)
    assert [t["title"] for t in tracker.list_tasks(path=f)] == ["B", "D"]


# M2 / RISK-02: a corrupted file gives a clear error and is never overwritten
@pytest.mark.parametrize("content", ["", '{"broken": ', "not json"])
def test_corrupted_file_raises_storage_error(tmp_path, content):
    f = tmp_path / "tasks.json"
    f.write_text(content, encoding="utf-8")
    with pytest.raises(storage.StorageError):
        storage.load_tasks(str(f))


def test_cli_reports_corrupted_file_and_keeps_it(tmp_path, monkeypatch, capsys):
    f = tmp_path / "tasks.json"
    f.write_text('{"broken": ', encoding="utf-8")
    monkeypatch.setenv("TASKS_FILE", str(f))
    code = cli.main(["add", "X"])
    err = capsys.readouterr().err
    assert code == 2
    assert "corrupted" in err
    assert f.read_text(encoding="utf-8") == '{"broken": '


def test_non_list_json_is_rejected(tmp_path):
    f = tmp_path / "tasks.json"
    f.write_text('{"id": 1}', encoding="utf-8")
    with pytest.raises(storage.StorageError):
        storage.load_tasks(str(f))
