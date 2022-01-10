#!/usr/bin/env python3

"""Manage ilastik development environment."""

import sys  # isort: skip

if sys.version_info[:2] < (3, 7):
    sys.exit("Python 3.7 or later is required")

import argparse
import logging
import shutil
import subprocess
import time

EXECUTABLES = ("mamba", "git")
REPOSITORIES = ("ilastik", "volumina")
DEFAULT_CREATE_ARGS = [
    "--channel",
    "ilastik-forge",
    "--channel",
    "conda-forge",
    "ilastik-dependencies-no-solvers",
    "pre-commit",
]

logging.basicConfig(format="%(asctime)s %(filename)s %(levelname)-10s %(message)s", level=logging.INFO)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap_sub = ap.add_subparsers(required=True, dest="cmd", metavar="cmd")

    ap_create = ap_sub.add_parser(
        "create",
        help="create a new environment",
        usage="%(prog)s [-h] [-n ENV] [arguments...]",
        epilog=(
            "All arguments will be added to the 'conda create' command.\n\n"
            "default arguments:\n  " + " ".join(DEFAULT_CREATE_ARGS)
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap_create.set_defaults(func=cmd_create)
    ap_create.add_argument("-n", "--name", metavar="ENV", help="environment name", default="ilastik")

    ap_remove = ap_sub.add_parser("remove", help="remove an existing environment")
    ap_remove.set_defaults(func=cmd_remove)
    ap_remove.add_argument("-n", "--name", metavar="ENV", help="environment name", default="ilastik")

    args, rest = ap.parse_known_args()

    if not all(map(shutil.which, EXECUTABLES)):
        sys.exit("the following executables should exist in the system path: " + str(EXECUTABLES)[1:-1])

    if not all(map(is_git_repo, REPOSITORIES)):
        sys.exit("the following directories should be valid git repositories: " + str(REPOSITORIES)[1:-1])

    logging.info("command %r started", args.cmd)
    time_start = time.perf_counter()

    try:
        args.func(args, rest)
    except subprocess.CalledProcessError:
        logging.error("command %r failed", args.cmd)
    except KeyboardInterrupt:
        logging.error("command %r interrupted", args.cmd)
    else:
        logging.info("command %r completed", args.cmd)

    time_end = time.perf_counter()
    logging.info("elapsed time: %.3f seconds", time_end - time_start)


def cmd_create(args, rest):
    chan_args = ["--override-channels", "--strict-channel-priority"]
    run(["mamba", "create", "--yes", "--name", args.name] + chan_args + (rest or DEFAULT_CREATE_ARGS) + ["boa"])

    for repo in REPOSITORIES:
        run(["conda", "develop", "--name", args.name, repo])
        run(["conda", "run", "--name", args.name, "pre-commit", "install"], cwd=repo)


def cmd_remove(args, _rest):
    run(["mamba", "env", "remove", "--yes", "--name", args.name])


def run(cmd, cwd=None):
    if cwd:
        logging.info("run command %r in directory %r", " ".join(cmd), cwd)
    else:
        logging.info("run command %r", " ".join(cmd))
    subprocess.run(cmd, stdout=sys.stdout, stderr=subprocess.STDOUT, cwd=cwd, check=True)


def is_git_repo(cwd):
    try:
        subprocess.check_call(["git", "rev-parse"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=cwd)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


if __name__ == "__main__":
    main()
