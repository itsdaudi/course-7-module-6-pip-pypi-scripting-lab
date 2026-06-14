from dataclasses import dataclass
import argparse
import json
from pathlib import Path


@dataclass
class Task:
    id: int
    user: str
    title: str
    completed: bool = False

    def mark_complete(self):
        self.completed = True

    def to_dict(self):
        return {
            "id": self.id,
            "user": self.user,
            "title": self.title,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            user=data["user"],
            title=data["title"],
            completed=data["completed"],
        )


class TaskStore:
    def __init__(self, path):
        self.path = Path(path)
        self.tasks = self._load()

    def _load(self):
        if not self.path.exists():
            return []

        with self.path.open("r") as file:
            return [Task.from_dict(item) for item in json.load(file)]

    def save(self):
        with self.path.open("w") as file:
            json.dump([task.to_dict() for task in self.tasks], file, indent=2)

    def add(self, task):
        self.tasks.append(task)
        self.save()

    def find(self, user, task_id):
        for task in self.tasks:
            if task.user == user and task.id == task_id:
                return task
        return None


class TaskManager:
    def __init__(self, store):
        self.store = store

    def add_task(self, user, title):
        if not user.strip():
            raise ValueError("user must not be empty")
        if not title.strip():
            raise ValueError("title must not be empty")

        next_id = max((task.id for task in self.store.tasks), default=0) + 1
        task = Task(id=next_id, user=user, title=title)
        self.store.add(task)
        return task

    def complete_task(self, user, task_id):
        task = self.store.find(user, task_id)
        if task is None:
            raise ValueError(f"Task #{task_id} not found for user {user}")

        task.mark_complete()
        self.store.save()
        return task


class TaskCLI:
    def __init__(self, store=None):
        self.store = store
        self.parser = self._build_parser()

    def _build_parser(self):
        parser = argparse.ArgumentParser(description="Manage user tasks")
        subparsers = parser.add_subparsers(dest="command", required=True)

        add_parser = subparsers.add_parser("add-task")
        add_parser.add_argument("--user", required=True)
        add_parser.add_argument("--title", required=True)

        complete_parser = subparsers.add_parser("complete-task")
        complete_parser.add_argument("--user", required=True)
        complete_parser.add_argument("--task-id", required=True, type=int)

        return parser

    def run(self, args=None):
        namespace = self.parser.parse_args(args)
        store = self.store or TaskStore("tasks.json")
        manager = TaskManager(store)

        if namespace.command == "add-task":
            task = manager.add_task(namespace.user, namespace.title)
            print(f"Task added: #{task.id} - {task.title}")
            return task

        task = manager.complete_task(namespace.user, namespace.task_id)
        print(f"Task completed: #{task.id} - {task.title}")
        return task


if __name__ == "__main__":
    cli = TaskCLI()
    cli.run()
