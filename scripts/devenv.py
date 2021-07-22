#!/usr/bin/env python3

"""Manage ilastik development environment."""

import argparse
import logging
import os
import shutil
import string
import subprocess
import sys
import time

if sys.version_info[:2] < (3, 7):
    sys.exit("Python 3.7 or later is required")

logging.basicConfig(
    format="%(asctime)s %(filename)s %(levelname)-10s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

REPOSITORIES = "ilastik", "volumina"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-n", "--name", metavar="ENV", help="environment name", default="ilastik")

    sub_ap = ap.add_subparsers(required=True, dest="cmd", metavar="cmd")

    create_ap = sub_ap.add_parser("create", help="create a new environment")
    create_ap.set_defaults(func=action_create)

    remove_ap = sub_ap.add_parser("remove", help="remove an existing environment")
    remove_ap.set_defaults(func=action_remove)

    args = ap.parse_args()

    if set(args.name).difference(string.ascii_letters + string.digits + "-_"):
        ap.error("environment name can contain only letters, digits, hyphens and underscores")

    if not shutil.which("conda"):
        sys.exit("conda not found in the system path")

    if not all([os.path.isdir(os.path.join(repo, ".git")) for repo in REPOSITORIES]):
        sys.exit(f"{REPOSITORIES} should be valid git repositories")

    time_start = time.perf_counter()

    try:
        args.func(args)
    except subprocess.CalledProcessError:
        logging.error("action failed")
    except KeyboardInterrupt:
        logging.error("action interrupted")
    else:
        logging.info("action completed")

    time_end = time.perf_counter()
    logging.info(f"elapsed time: {time_end - time_start:.3f} seconds")


def action_create(args):
    run("conda install --yes --name base --channel conda-forge conda-build")
    run(
        f"conda create --yes --name {args.name} --channel ilastik-forge --channel conda-forge ilastik-dependencies-no-solvers pre-commit"
    )

    for repo in REPOSITORIES:
        run(f"conda develop --name {args.name} {repo}")
        run(f"conda run --name {args.name} pre-commit install", cwd=repo)


def action_remove(args):
    run(f"conda remove --yes --name {args.name}")


def run(cmd, *, cwd=None):
    if cwd:
        logging.info(f"run command {cmd!r} in working directory {cwd!r}")
    else:
        logging.info(f"run command {cmd!r}")

    stdout = sys.stdout
    stderr = subprocess.STDOUT
    subprocess.run(cmd.split(), stdout=stdout, stderr=stderr, cwd=cwd, check=True)


if __name__ == "__main__":
    main()
