#!/usr/bin/env python3

"""Utility to reset best_values for a task's datasets.

"""

import argparse
import logging
import sys

from cms import utf8_decoder
from cms.db import SessionGen, Task, ask_for_contest


logger = logging.getLogger(__name__)


def reset_best_values(task_name, contest_id):
    with SessionGen() as session:
        query = session.query(Task).filter(Task.name == task_name)
        if contest_id is not None:
            query = query.filter(Task.contest_id == contest_id)
        task = query.first()

        if task is None:
            logger.error("No task called `%s' found.", task_name)
            return False

        for dataset in task.datasets:
            logger.info("Resetting best_values for dataset %d (%s) of task `%s'.",
                        dataset.id, dataset.description, task_name)
            dataset.best_values = {}

        session.commit()
        logger.info("Done.")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Reset best_values for a task's datasets.")
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

    success = reset_best_values(
        task_name=args.task_name,
        contest_id=contest_id,
    )
    return 0 if success is True else 1


if __name__ == "__main__":
    sys.exit(main())
