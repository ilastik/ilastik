from fs.errors import ResourceNotFound
import uuid
import sys
from pathlib import Path
from threading import Thread
import functools

from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler

import pytest

from ilastik.filessytem import HttpPyFs


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def create_test_dir(tmp_path: Path, server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler):
    dir1 = tmp_path / "dir1"
    dir1.mkdir()
    with open(dir1 / "file1.txt", "wb") as f:
        f.write("file1_contents".encode("ascii"))

    dir2 = tmp_path / "dir2"
    dir2.mkdir()
    with open(dir2 / "file2.txt", "wb") as f:
        f.write("file2_contents".encode("ascii"))

    dir3 = tmp_path / "dir3"
    dir3.mkdir()
    with open(dir3 / "file3.txt", "wb") as f:
        f.write("file3_contents".encode("ascii"))

    dir4 = dir3 / "dir4"
    dir4.mkdir()
    with open(dir4 / "file4.txt", "wb") as f:
        f.write("file4_contents".encode("ascii"))

    server_address = ("", 8123)
    httpd = server_class(server_address, functools.partial(SimpleHTTPRequestHandler, directory=tmp_path.as_posix()))
    Thread(target=httpd.serve_forever).start()


def test_httpfs(tmp_path):
    create_test_dir(tmp_path)
    fs = HttpPyFs("http://localhost:8123/")

    eprint("  -->  Opening some file...")
    # import pydevd; pydevd.settrace()
    with fs.openbin("/dir1/file1.txt", "r") as f:
        assert f.read() == "file1_contents".encode("ascii")

    eprint("  --> Verifying that opendir works nested dirs...")
    dir1 = fs.opendir("dir2")
    assert dir1.openbin("file2.txt", "r").read() == "file2_contents".encode("ascii")

    fs2 = HttpPyFs("http://localhost:8123/dir1")
    assert fs2.desc("file2.txt") == "http://localhost:8123/dir1/file2.txt"

    # check that "/" maps to the base url that was used to create the filesystem
    assert fs2.desc("/file2.txt") == "http://localhost:8123/dir1/file2.txt"
