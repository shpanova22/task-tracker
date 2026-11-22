import argparse
import sys

from . import priority, storage, tracker


def format_task(t):
    mark = priority.mark(t["priority"])
    status = "[x]" if t["done"] else "[ ]"
    due = f" (due {t['due']})" if t["due"] else ""
    return f"{t['id']:>3} {status} {mark:<3} {t['title']}{due}"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="tasktracker", description="Simple task tracker")
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="add a task")
    p_add.add_argument("title")
    p_add.add_argument("--priority", default="medium")
    p_add.add_argument("--due", help="YYYY-MM-DD")

    p_done = sub.add_parser("done", help="mark task as done")
    p_done.add_argument("id", type=int)

    p_del = sub.add_parser("delete", help="delete a task")
    p_del.add_argument("id", type=int)

    p_list = sub.add_parser("list", help="list tasks")
    p_list.add_argument("--pending", action="store_true")
    p_list.add_argument("--sort", default="id", choices=sorted(tracker.SORT_KEYS))

    sub.add_parser("overdue", help="show overdue tasks")

    args = parser.parse_args(argv)
    try:
        return _run(args, parser)
    except storage.StorageError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


def _run(args, parser):
    if args.command == "add":
        t = tracker.add_task(args.title, args.priority, args.due)
        print(f"Added task {t['id']}: {t['title']}")
    elif args.command == "done":
        t = tracker.complete_task(args.id)
        if t:
            print(f"Completed task {t['id']}")
        else:
            print("Task not found")
            return 1
    elif args.command == "delete":
        if tracker.delete_task(args.id):
            print(f"Deleted task {args.id}")
        else:
            print("Task not found")
            return 1
    elif args.command == "list":
        for t in tracker.list_tasks(show_done=not args.pending, sort_by=args.sort):
            print(format_task(t))
    elif args.command == "overdue":
        for t in tracker.overdue_tasks():
            print(format_task(t))
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
