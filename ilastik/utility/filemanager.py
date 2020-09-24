import os
import shutil
import subprocess
import sys
from typing import Union


def open(path: Union[str, bytes, os.PathLike]):
    """Open a path in the system's default file manager or program."""
    if sys.platform == "win32":
        os.startfile(path)
        return

    if sys.platform == "linux":
        cmd = "xdg-open"
    elif sys.platform == "darwin":
        cmd = "open"
    else:
        raise RuntimeError(f"unsupported platform {sys.platform}")

    cmd = shutil.which(cmd)
    if cmd is None:
        raise MissingProgramError(cmd)

    _run(cmd, path)


class MissingProgramError(RuntimeError):
    def __init__(self, name):
        super().__init__(f"Program {name} is not installed")
        self.name = name


def _run(*args):
    exitcode = subprocess.Popen(
        args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True
    ).wait()
    if exitcode:
        raise subprocess.CalledProcessError(exitcode, args)
