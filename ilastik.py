import os
import pathlib
import platform
import shlex
import sys
from typing import Iterable, Mapping, Sequence, Tuple, Union


def _env_list(name: str, sep: str = os.pathsep) -> Iterable[str]:
    """Items from the environment variable, delimited by separator.

    Empty sequence if the variable is not set.
    """
    value = os.environ.get(name, "")
    if not value:
        return []
    return value.split(sep)


def _clean_paths(root: pathlib.Path) -> None:
    def issubdir(path):
        """Whether path is equal to or is a subdirectory of root."""
        path = pathlib.PurePath(path)
        return path == root or any(parent == root for parent in path.parents)

    def subdirs(*suffixes):
        """Valid subdirectories of root."""
        paths = map(root.joinpath, suffixes)
        return [str(p) for p in paths if p.is_dir()]

    def isvalidpath_win(path):
        """Whether an element of PATH is "clean" on Windows."""

        def partial_match(path, pattern):
            """allow arbitrary nesting within those patterns"""
            return any(p.match(pattern) for p in path.parents)

        patterns = "**/cplex_studio*", "**/gurobi*", "/windows/system32/*"
        return any(partial_match(pathlib.PurePath(path), pat) for pat in patterns)

    # Remove undesired paths from PYTHONPATH and add ilastik's submodules.
    sys_path = list(filter(issubdir, sys.path))
    sys_path += subdirs("ilastik/lazyflow", "ilastik/volumina", "ilastik/ilastik")
    sys.path = sys_path

    if sys.platform.startswith("win"):
        # Empty PATH except for gurobi and CPLEX and add ilastik's installation paths.
        path = list(filter(isvalidpath_win, _env_list("PATH")))
        path += subdirs("Library/bin", "Library/mingw-w64/bin", "python", "bin")
        os.environ["PATH"] = os.pathsep.join(reversed(path))
    else:
        # Clean LD_LIBRARY_PATH and add ilastik's installation paths
        # (gurobi and CPLEX are supposed to be located there as well).
        ld_lib_path = list(filter(issubdir, _env_list("LD_LIBRARY_PATH")))
        ld_lib_path += subdirs("lib")
        os.environ["LD_LIBRARY_PATH"] = os.pathsep.join(reversed(ld_lib_path))


def _parse_internal_config(path: Union[str, os.PathLike]) -> Tuple[Sequence[str], Mapping[str, str]]:
    """Parse options from the internal config file.

    Args:
        path: Path to the config file.

    Returns:
        Additional command-line options and environment variable assignments.
        Both are empty if the config file does not exist.

    Raises:
        ValueError: Config file is malformed.
    """
    path = pathlib.Path(path)
    if not path.exists():
        return [], {}

    opts = shlex.split(path.read_text(), comments=True)

    sep_idx = tuple(i for i, opt in enumerate(opts) if opt.startswith(";"))
    if len(sep_idx) != 1:
        raise ValueError(f"{path} should have one and only one semicolon separator")
    sep_idx = sep_idx[0]

    env_vars = {}
    for opt in opts[:sep_idx]:
        name, sep, value = opt.partition("=")
        if not name or not sep:
            raise ValueError(f"invalid environment variable assignment {opt!r}")
        env_vars[name] = value

    return opts[sep_idx + 1 :], env_vars


def path_setup():
    if "--clean_paths" in sys.argv:
        script_dir = pathlib.Path(__file__).parent
        ilastik_root = script_dir.parent.parent
        _clean_paths(ilastik_root)

    # Allow to start-up by double-clicking a project file.
    if len(sys.argv) == 2 and sys.argv[1].endswith(".ilp"):
        sys.argv.insert(1, "--project")

    arg_opts, env_vars = _parse_internal_config("internal-startup-options.cfg")
    sys.argv[1:1] = arg_opts
    os.environ.update(env_vars)


def main():
    path_setup()

    # https://bugreports.qt.io/browse/QTBUG-87014
    if platform.mac_ver()[0] == "10.16":
        os.environ["QT_MAC_WANTS_LAYER"] = "1"

    from ilastik.__main__ import main

    main()


if __name__ == "__main__":
    main()
