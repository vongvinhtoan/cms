#!/usr/bin/env python3

"""Utility to display best_values for a task's datasets.

"""

import argparse
import json
import logging
import sys

from cms import utf8_decoder
from cms.db import SessionGen, Task, ask_for_contest


logger = logging.getLogger(__name__)


def show_best_values(task_name, contest_id):
    with SessionGen() as session:
        query = session.query(Task).filter(Task.name == task_name)
        if contest_id is not None:
            query = query.filter(Task.contest_id == contest_id)
        task = query.first()

        if task is None:
            logger.error("No task called `%s' found.", task_name)
            return False

        for dataset in task.datasets:
            best_values = dataset.best_values or {}
            if not best_values:
                print("Dataset %d (%s): no best_values" %
                      (dataset.id, dataset.description))
                continue

            codenames = sorted(best_values.keys())
            col_w = max(len(c) for c in codenames)
            col_w = max(col_w, len("codename"))
            val_w = max(len("%.12f" % best_values[c]) for c in codenames)
            val_w = max(val_w, len("best_value"))

            print("Dataset %d (%s):" % (dataset.id, dataset.description))
            print("  %s  %s" % ("codename".ljust(col_w), "best_value".rjust(val_w)))
            print("  %s  %s" % ("-" * col_w, "-" * val_w))
            for c in codenames:
                print("  %s  %s" % (c.ljust(col_w), ("%.12f" % best_values[c]).rjust(val_w)))
            print()

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Display best_values for a task's datasets.")
    parser.add_argument(
        "task_name",
        action="store", type=utf8_decoder,
        help="short name of the task")
    parser.add_argument(
        "-c", "--contest-id",
        action="store", type=int,
        help="id of the contest (optional)")

    args = parser.parse_args()

    contest_id = args.contest_id
    if contest_id is None:
        contest_id = ask_for_contest()

    success = show_best_values(
        task_name=args.task_name,
        contest_id=contest_id,
    )
    return 0 if success is True else 1


if __name__ == "__main__":
    sys.exit(main())
