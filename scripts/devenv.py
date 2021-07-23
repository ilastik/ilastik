#!/usr/bin/env python3

"""Manage ilastik development environment."""

import sys  # isort: skip

if sys.version_info[:2] < (3, 8):
    sys.exit("Python 3.8 or later is required")

import argparse
import logging
import os
import shlex
import shutil
import subprocess
import time

EXECUTABLES = "conda", "git"
REPOSITORIES = "ilastik", "volumina"

logging.basicConfig(format="%(asctime)s %(filename)s %(levelname)-10s %(message)s", level=logging.INFO)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-n", "--name", metavar="ENV", help="environment name", default="ilastik", required=True)
    sub_ap = ap.add_subparsers(required=True, dest="cmd", metavar="cmd")
    sub_ap.add_parser("create", help="create a new environment").set_defaults(func=action_create)
    sub_ap.add_parser("remove", help="remove an existing environment").set_defaults(func=action_remove)
    args = ap.parse_args()

    if not all(map(shutil.which, EXECUTABLES)):
        sys.exit("executables " + punctlist(EXECUTABLES) + " should exist in the system path")

    if not all(map(is_git_repo, REPOSITORIES)):
        sys.exit("directories " + punctlist(REPOSITORIES) + " should be valid git repositories")

    logging.info("command %r started", args.cmd)
    time_start = time.perf_counter()

    try:
        args.func(args)
    except subprocess.CalledProcessError:
        logging.error("command %r failed", args.cmd)
    except KeyboardInterrupt:
        logging.error("command %r interrupted", args.cmd)
    else:
        logging.info("command %r completed", args.cmd)

    time_end = time.perf_counter()
    logging.info("elapsed time: %.3f seconds", time_end - time_start)


def action_create(args):
    run(["conda", "install", "--yes", "--name", "base", "--channel", "conda-forge", "conda-build"])

    chans = ["--channel", "ilastik-forge", "--channel", "conda-forge"]
    pkgs = ["ilastik-dependencies-no-solvers", "pre-commit"]
    run(["conda", "create", "--yes", "--name", args.name] + chans + pkgs)

    for repo in REPOSITORIES:
        run(["conda", "develop", "--name", args.name, repo])
        run(["conda", "run", "--name", args.name, "pre-commit", "install"], cwd=repo)


def action_remove(args):
    run(["conda", "env", "remove", "--yes", "--name", args.name])


def run(cmd, cwd=None):
    msg = "run command " + repr(shlex.join(cmd))
    if cwd:
        msg += " in working directory " + repr(cwd)
    logging.info(msg)
    subprocess.run(cmd, stdout=sys.stdout, stderr=subprocess.STDOUT, cwd=cwd, check=True)


def is_git_repo(cwd):
    if not os.path.isdir(cwd):
        return False
    proc = subprocess.run(["git", "rev-parse"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=cwd)
    return proc.returncode == 0


def punctlist(seq):
    if not seq:
        raise ValueError("empty sequence")
    if len(seq) == 1:
        return repr(seq[0])
    return ", ".join(map(repr, seq[:-1])) + " and " + repr(seq[-1])


if __name__ == "__main__":
    main()
