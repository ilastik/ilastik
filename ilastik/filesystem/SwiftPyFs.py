import re
from pathlib import Path
import io
from typing import Dict, Iterable, List, Any, Callable, Optional, Tuple

from fs.base import FS
from fs.subfs import SubFS
from fs.info import Info
from fs.errors import DirectoryExpected, FileExpected, ResourceNotFound
from fs.permissions import Permissions
from fs.enums import ResourceType

from swiftclient.exceptions import ClientException
from swiftclient.client import Connection
import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class SwiftFile(io.BytesIO):
    def __init__(self, close_callback: Callable[["SwiftFile"], None], mode: str, data: bytes):
        super().__init__()
        self.mode = mode
        self.close_callback = close_callback
        super().__init__(data)

    def write(self, data: bytes):
        if self.mode == "r":
            raise RuntimeError("This is a readonly file!")
        super().write(data)

    def close(self):
        self.close_callback(self)
        super().close()


class SwiftPyFs(FS):
    def __init__(self, swift_connection: Connection, container: str, prefix: str = "/"):
        self.connection = swift_connection
        self.container = container
        self.prefix = Path(prefix)
        if not self.prefix.is_absolute():
            raise ValueError("Prefix must start with '/'")

    def desc(self, path: str) -> str:
        return self._make_full_path(path)

    def _make_full_path(self, path: str, add_trailing_slash=False) -> str:
        "Creates an absolute path representing 'path'"
        clean_path = re.sub("^/", "", Path("/").joinpath(path).resolve(strict=False).as_posix())
        return self.prefix.joinpath(clean_path).as_posix()

    def _delete_object(self, path: str) -> None:
        full_path = self._make_full_path(path)
        eprint(f"Removing object at {full_path}")
        self.connection.delete_object(self.container, full_path[1:])

    def _put_object(self, path: str, contents: bytes) -> str:
        full_path = self._make_full_path(path)
        resource_type = self._get_type(full_path)
        if resource_type == ResourceType.file:
            eprint(f"Overwriting object at {full_path}")
            self._delete_object(full_path)
        elif resource_type == ResourceType.directory:
            raise ValueError(f"{full_path} is a directory")
        assert full_path != "/"
        return self.connection.put_object(self.container, full_path[1:], contents)

    def _get_container(self, prefix: str, limit: int = 0) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
        full_path = self._make_full_path(prefix)[1:]
        full_path += "/" if full_path != "" else ""
        params = {"limit": limit} if limit else {}
        return self.connection.get_container(self.container, prefix=full_path, delimiter="/", **params)

    def _get_object(self, path: str) -> Tuple[Dict[str, str], bytes]:
        full_path = self._make_full_path(path)
        return self.connection.get_object(self.container, full_path[1:])

    def _head_object(self, path: str) -> Dict:
        full_path = self._make_full_path(path)
        return self.connection.head_object(self.container, full_path[1:])

    def _get_type(self, path: str) -> ResourceType:
        full_path = self._make_full_path(path)
        if full_path == "/":
            return ResourceType.directory
        try:
            self._head_object(path)
            return ResourceType.file
        except ClientException:
            pass

        _, entries = self._get_container(path, limit=1)
        if len(entries) > 0:
            return ResourceType.directory
        return ResourceType.unknown

    def getinfo(self, path: str, namespaces: Iterable[str] = ("basic",)) -> Info:
        full_path = self._make_full_path(path)
        resource_type = self._get_type(full_path)
        if resource_type == ResourceType.unknown:
            raise ResourceNotFound(full_path)
        return Info(
            raw_info={
                "basic": {
                    "name": Path(full_path).name,
                    "is_dir": True if resource_type == ResourceType.directory else False,
                },
                "details": {"type": resource_type},
            }
        )

    def listdir(self, path: str) -> List[str]:
        """Get a list of the resource names in a directory.

        This method will return a list of the resources in a directory.
        A *resource* is a file, directory, or one of the other types
        defined in `~fs.enums.ResourceType`.

        Arguments:
            path (str): A path to a directory on the filesystem

        Returns:
            list: list of names, relative to ``path``.

        Raises:
            fs.errors.DirectoryExpected: If ``path`` is not a directory.
            fs.errors.ResourceNotFound: If ``path`` does not exist.

        """
        if self._get_type(path) != ResourceType.directory:
            raise DirectoryExpected(path)
        _, entries = self._get_container(path)

        full_path = self._make_full_path(path)
        prefix = full_path[1:]  # drop leading slash
        prefix += "/" if prefix else ""
        return [(entry.get("subdir") or entry["name"])[len(prefix) :] for entry in entries]

    def makedir(
        self, path: str, permissions: Optional[Permissions] = None, recreate: bool = False
    ) -> SubFS["SwiftPyFs"]:
        """Make a directory.

        Arguments:
            path (str): Path to directory from root.
            permissions (~fs.permissions.Permissions, optional): a
                `Permissions` instance, or `None` to use default.
            recreate (bool): Set to `True` to avoid raising an error if
                the directory already exists (defaults to `False`).

        Returns:
            ~fs.subfs.SubFS: a filesystem whose root is the new directory.

        Raises:
            fs.errors.DirectoryExists: If the path already exists.
            fs.errors.ResourceNotFound: If the path is not found.

        """
        # Makedir makes no sense in swift... but maybe we should create a placeholder obj?"
        return self.opendir(path)

    def openbin(self, path: str, mode: str = "r", buffering: int = -1, **options: Dict[str, Any]) -> SwiftFile:
        def close_callback(f: SwiftFile):
            if mode != "r":
                f.seek(0)
                self._put_object(path, f.read())

        try:
            meta, contents = self._get_object(path)
            swift_file = SwiftFile(close_callback=close_callback, mode=mode, data=contents)
            if mode.startswith("a"):
                swift_file.seek(0, io.SEEK_END)
            return swift_file
        except ClientException as e:
            if e.http_status == 404:
                if mode in ("r", "r+"):
                    raise ResourceNotFound(path) from e
                return SwiftFile(close_callback=close_callback, mode=mode, data=bytes())
            raise e

    def remove(self, path: str) -> None:
        """Remove a file from the filesystem.

        Arguments:
            path (str): Path of the file to remove.

        Raises:
            fs.errors.FileExpected: If the path is a directory.
            fs.errors.ResourceNotFound: If the path does not exist.

        """
        full_path = self._make_full_path(path)
        if self._get_type(path) != ResourceType.file:
            raise FileExpected(full_path)
        try:
            self._delete_object(path)
        except ClientException as e:
            if e.http_status == 404:
                raise ResourceNotFound(full_path)

    def removedir(self, path: str) -> None:
        """Remove a directory from the filesystem.

        Arguments:
            path (str): Path of the directory to remove.

        Raises:
            fs.errors.DirectoryNotEmpty: If the directory is not empty (
                see `~fs.base.FS.removetree` for a way to remove the
                directory contents.).
            fs.errors.DirectoryExpected: If the path does not refer to
                a directory.
            fs.errors.ResourceNotFound: If no resource exists at the
                given path.
            fs.errors.RemoveRootError: If an attempt is made to remove
                the root directory (i.e. ``'/'``)

        """
        raise NotImplementedError("removedir")

    def setinfo(self, path, info):
        # type: (Text, RawInfo) -> None
        """Set info on a resource.

        This method is the complement to `~fs.base.FS.getinfo`
        and is used to set info values on a resource.

        Arguments:
            path (str): Path to a resource on the filesystem.
            info (dict): Dictionary of resource info.

        Raises:
            fs.errors.ResourceNotFound: If ``path`` does not exist
                on the filesystem

        The ``info`` dict should be in the same format as the raw
        info returned by ``getinfo(file).raw``.

        Example:
            >>> details_info = {"details": {
            ...     "modified": time.time()
            ... }}
            >>> my_fs.setinfo('file.txt', details_info)

        """
        raise NotImplementedError("setinfo")
