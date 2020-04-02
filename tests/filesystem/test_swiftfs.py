import SwiftTestConnection
from fs_swift.SwiftPyFs import SwiftPyFs
from fs.errors import ResourceNotFound
import uuid
import sys

import pytest


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def test_swiftfs():
    swift_connection = SwiftTestConnection.get_connection()
    container_name = SwiftTestConnection.get_container_name()

    fs = SwiftPyFs(swift_connection=swift_connection, container=container_name)

    eprint("")
    eprint("  --> cleanup...")
    for obj in fs.glob("**/*.txt"):
        fs.remove(obj.path)

    eprint("  --> test writing")
    test_data = str(uuid.uuid4()).encode("utf8")
    with fs.openbin("myfile.txt", "w") as filelike:
        filelike.write(test_data)

    eprint("  --> verify writing was successful")
    with fs.openbin("myfile.txt") as filelike:
        retrieved_data = filelike.read()
        assert retrieved_data == test_data

    eprint("  --> test appending")
    extra_data = str(uuid.uuid4()).encode("utf8")
    with fs.openbin("myfile.txt", "a") as filelike:
        filelike.write(extra_data)

    eprint("  --> verify appending was successful")
    with fs.openbin("myfile.txt") as filelike:
        retrieved_data = filelike.read()
        assert retrieved_data == test_data + extra_data

    eprint("  --> verify can't open non-existant files as readonly")
    with pytest.raises(ResourceNotFound):
        fs.openbin("my_non-existing_file.txt", "r")

    eprint("  --> Creating some nested directories...")
    with fs.openbin("/dir1/dir2/dir3/test.txt", "w") as f:
        f.write("test".encode("ascii"))

    eprint("  --> Verifying that opendir works nested dirs...")
    dir1 = fs.opendir("dir1")
    assert dir1.listdir("") == ["dir2/"]

    dir2 = dir1.opendir("dir2/")
    assert dir2.listdir("") == ["dir3/"]

    eprint("  --> Verifying that opendir works with root dir...")
    top_dir = fs.opendir("/")
    assert sorted(top_dir.listdir("")) == sorted(fs.listdir(""))

    assert sorted(fs.listdir("")) == sorted(["myfile.txt", "dir1/"])
