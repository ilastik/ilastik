#!/usr/bin/env python

"""Manage ilastik development environment."""

import sys

# Don't use new language features when checking the minimum Python version.
if sys.version_info < (3, 6):
    sys.stderr.write("Python 3.6 or later is required.\n")
    sys.exit(1)

import argparse
import collections
import contextlib
import json
import logging
import os
import pathlib
import shutil
import subprocess
import time
from typing import Any, Callable, Iterable, Optional


logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(filename)s %(levelname)-10s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    level=logging.INFO,
)


def run(*args: Optional[str]) -> None:
    """Execute the command; fail on non-zero exit code.

    Arguments that are None are omitted from the command's argument list.
    """
    args = [arg for arg in args if arg is not None]
    subprocess.run(args, check=True, encoding="utf-8")


def run_stdout(*args: Optional[str]) -> str:
    """:func:`run` that returns the standard output and ignores the standard error."""
    args = [arg for arg in args if arg is not None]
    proc = subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, encoding="utf-8")
    return proc.stdout


class CondaEnv:
    """Environment in the conda package manager.

    Attributes:
        name: Name of the target conda environment.
    """

    def __init__(self, name: str):
        self.name = name
        self._info_cache = None

    def __repr__(self):
        return f"{__class__.__name__}({self.name!r})"

    def exists(self) -> bool:
        """Does this environment exist?"""
        try:
            _path = self.prefix_path
            return True
        except ValueError:
            return False

    def create(self, *, packages: Iterable[str], channels: Iterable[str] = ()) -> None:
        """Create this environment.

        Args:
            packages: Package specs to install (package names and versions).
            channels: Additional channels to use.
        """
        chan_args = []
        for chan in channels:
            chan_args += ["--channel", chan]
        run("conda", "create", "--yes", "--name", self.name, *chan_args, *packages)
        self._info_cache = None

    def remove(self) -> None:
        """Remove this environment."""
        run("conda", "env", "remove", "--yes", "--name", self.name)
        self._info_cache = None

    def remove_package(self, package: str, *, force=False) -> None:
        """Remove a package in this environment."""
        run("conda", "remove", "--yes", "--force" if force else None, "--name", self.name, package)

    def develop(self, path: pathlib.Path):
        run("conda", "develop", "--name", self.name, str(path))

    @property
    def _info(self):
        if self._info_cache is not None:
            return self._info_cache
        info_raw = run_stdout("conda", "info", "--json")
        info_json = json.loads(info_raw)
        if not isinstance(info_json, collections.abc.Mapping):
            raise json.JSONDecodeError("not a JSON dictionary", doc=info_raw, pos=0)
        self._info_cache = info_json
        return self._info_cache

    @property
    def prefix_path(self) -> pathlib.Path:
        """Installation directory for this environment.

        Raises:
            ValueError: The current environment does not exist.
        """
        prefixes = [pathlib.Path(d) for d in self._info["envs_dirs"]]
        for env in self._info["envs"]:
            env = pathlib.Path(env)
            for prefix in prefixes:
                with contextlib.suppress(ValueError):
                    if str(env.relative_to(prefix)) == self.name:
                        return env
        raise ValueError("environment does not exist")

    @property
    def site_packages_path(self) -> pathlib.Path:
        """Python site-packages directory for this environment."""
        # Execute another Python interpreter: need to get their "site-packages" location.
        if os.name == "posix":
            python_path = self.prefix_path / "bin" / "python"
        elif os.name == "nt":
            python_path = self.prefix_path / "python"
        else:
            raise RuntimeError(f"unsupported os.name {os.name}")
        script = r"import site; print('\n'.join(site.getsitepackages()))"
        lines = run_stdout(str(python_path), "-c", script).splitlines()
        if not lines:
            raise RuntimeError("no 'site-packages' directories")
        return pathlib.Path(lines[0])


class ReplaceAction(argparse.Action):
    """Replace the previous or default stored value."""

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


def timed(func: Callable, *args: Any, **kwargs: Any) -> (float, Any):
    """Measure the execution time of a function call.

    Returns:
        2-tuple of execution time in seconds and function's actual result.
    """
    start = time.perf_counter()
    res = func(*args, **kwargs)
    end = time.perf_counter()
    return end - start, res


def main():
    def add_global_args(argparser: argparse.ArgumentParser) -> None:
        argparser.add_argument("-n", "--name", help="name of the conda environment", default="ilastik-devel")

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    sub = ap.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    create_ap = sub.add_parser(
        "create", help="create a new development environment", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    create_ap.set_defaults(func=command_create)
    add_global_args(create_ap)
    create_ap.add_argument(
        "-p",
        "--package",
        help="conda packages to install",
        metavar="PKG",
        nargs="*",
        default=["ilastik-dependencies-no-solvers"],
        action=ReplaceAction,
    )
    create_ap.add_argument(
        "-c",
        "--channel",
        help="conda channels to use",
        metavar="CHAN",
        nargs="*",
        default=["ilastik-forge", "conda-forge"],
        action=ReplaceAction,
    )
    create_ap.add_argument(
        "-l",
        "--location",
        help="local ilastik-meta directory",
        metavar="DIR",
        nargs="?",
        const=None,
        default=str(pathlib.Path(".").resolve()),
    )

    remove_ap = sub.add_parser(
        "remove",
        help="remove an existing development environment",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    remove_ap.set_defaults(func=command_remove)
    add_global_args(remove_ap)

    args = ap.parse_args()

    if shutil.which("conda") is None:
        logging.error("conda is not installed")
        return

    env = CondaEnv(args.name)
    execution_time, _res = timed(args.func, args, env)
    logging.info(f"finished {args.command} ({execution_time:.3f} seconds)")


def command_create(args: argparse.Namespace, env: CondaEnv) -> None:
    if env.exists():
        logging.error(f"environment {env.name} already exists")
        return

    location = args.location
    if location is not None:
        location = pathlib.Path(location).resolve()
        if not location.is_dir():
            logging.error(f"{location} is not a valid directory")
            return

    logging.info(
        f"create environment {env.name}"
        f" with packages [{', '.join(args.package)}]"
        f" from channels [{', '.join(args.channel)}]"
    )
    env.create(packages=args.package, channels=args.channel)

    if location is None:
        return

    packages = "lazyflow", "volumina", "ilastik"
    package_locations = [location / pkg for pkg in packages]

    for package_location in package_locations:
        env.develop(package_location)


def command_remove(_args: argparse.Namespace, env: CondaEnv) -> None:
    if not env.exists():
        logging.error(f"environment {env.name} not found")
        return

    logging.info(f"remove environment {env.name}")
    env.remove()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        main()
