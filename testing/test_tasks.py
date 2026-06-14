import json
import pytest

from lib.tasks import Task, TaskCLI, TaskManager, TaskStore


@pytest.fixture
def store(tmp_path):
    return TaskStore(tmp_path / "tasks.json")


@pytest.fixture
def manager(store):
    return TaskManager(store)


def test_add_task_creates_task_for_user(manager):
    task = manager.add_task("audi", "Write CLI tool")

    assert task.id == 1
    assert task.user == "audi"
    assert task.title == "Write CLI tool"
    assert task.completed is False


def test_complete_task_marks_task_complete(manager):
    task = manager.add_task("audi", "Write CLI tool")

    completed_task = manager.complete_task("audi", task.id)

    assert completed_task.completed is True
    assert manager.store.find("audi", task.id).completed is True


def test_complete_task_rejects_missing_task(manager):
    with pytest.raises(ValueError, match="Task #1 not found"):
        manager.complete_task("audi", 1)


def test_task_store_persists_tasks(tmp_path):
    store = TaskStore(tmp_path / "tasks.json")
    manager = TaskManager(store)
    task = manager.add_task("audi", "Write CLI tool")

    reloaded_store = TaskStore(tmp_path / "tasks.json")
    reloaded_task = reloaded_store.find("audi", task.id)

    assert reloaded_task.title == "Write CLI tool"
    assert reloaded_task.completed is False


def test_task_store_persists_completed_tasks(tmp_path):
    store = TaskStore(tmp_path / "tasks.json")
    manager = TaskManager(store)
    task = manager.add_task("audi", "Write CLI tool")
    manager.complete_task("audi", task.id)

    with (tmp_path / "tasks.json").open("r") as file:
        data = json.load(file)

    assert data == [
        {
            "id": 1,
            "user": "audi",
            "title": "Write CLI tool",
            "completed": True,
        }
    ]


def test_cli_add_task_writes_feedback_and_file(tmp_path, capsys):
    cli = TaskCLI(TaskStore(tmp_path / "tasks.json"))

    task = cli.run(["add-task", "--user", "audi", "--title", "Write CLI tool"])

    assert task.id == 1
    assert capsys.readouterr().out.strip() == "Task added: #1 - Write CLI tool"
    assert TaskStore(tmp_path / "tasks.json").find("audi", 1).title == "Write CLI tool"


def test_cli_complete_task_writes_feedback_and_file(tmp_path, capsys):
    cli = TaskCLI(TaskStore(tmp_path / "tasks.json"))
    cli.run(["add-task", "--user", "audi", "--title", "Write CLI tool"])
    capsys.readouterr()

    task = cli.run(["complete-task", "--user", "audi", "--task-id", "1"])

    assert task.completed is True
    assert capsys.readouterr().out.strip() == "Task completed: #1 - Write CLI tool"
    assert TaskStore(tmp_path / "tasks.json").find("audi", 1).completed is True
