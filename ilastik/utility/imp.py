"""Custom importlib-like utilities."""

import contextlib
import importlib.abc
import sys
import traceback
from typing import Optional, Tuple


class ImportBlacklist(importlib.abc.MetaPathFinder):
    """Prevent importing of certain modules.

    Use Python's import system to prevent modules from being imported.
    Create a blacklist and call :meth:`install` to enable it.
    When someone tries to import a blacklisted module, :exc:`ModuleBlacklistedError` will be thrown.

    When using the blacklist as a contextmanager, the module will be blacklisted only inside the "with" block.

    Attributes:
        blacklist: Blacklisted module names.
    """

    blacklist: Tuple[str]

    def __init__(self, *blacklist: str):
        """Create a new blacklist."""
        self.blacklist = blacklist
        self._caller: Optional[traceback.FrameSummary] = None

    def find_spec(self, fullname, _path, _target=None):
        assert self._caller is not None, f"{self} is not installed"
        if fullname not in self.blacklist:
            return None
        raise BlacklistedModuleError(fullname, self._caller)

    def install(self) -> None:
        """Add this blacklist to the front of :data:`sys.meta_path`.

        If this blacklist has been already installed, just move it to the front.

        Raises:
            RuntimeError: Some of the blacklisted modules are already imported (that is, found in :data:`sys.modules`).
        """
        imported = tuple(filter(sys.modules.__contains__, self.blacklist))
        if imported:
            raise AlreadyImportedError(*imported)
        self.uninstall()
        sys.meta_path.insert(0, self)
        self._caller = traceback.extract_stack(limit=2)[0]

    def uninstall(self) -> None:
        """Remove this blacklist from :data:`sys.meta_path` if it has been installed."""
        with contextlib.suppress(ValueError):
            sys.meta_path.remove(self)
        self._caller = None

    def __enter__(self):
        self.install()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.uninstall()

    def __repr__(self):
        name = f"{type(self).__module__}.{type(self).__qualname__}"
        args = ', '.join(map(repr, self.blacklist))
        return f"{name}({args})"


class BlacklistedModuleError(ImportError):
    """Module cannot be imported because it has been blacklisted by :cls:`ImportBlacklist`.

    Attributes:
        fullname: Name of the blacklisted module.
        caller: Where the module has been blacklisted.
    """

    fullname: str
    caller: Optional[traceback.FrameSummary]

    def __init__(self, fullname, caller=None):
        self.fullname = fullname
        self.caller = caller

    def __str__(self):
        s = f"Module {self.fullname!r} is blacklisted"
        if self.caller:
            s += f" in {self.caller.filename}:{self.caller.lineno}: {self.caller.line}"
        return s


class AlreadyImportedError(ImportError):
    """Some blacklisted modules are already imported during :meth:`ImportBlacklist.install`.

    Attributes:
        modules: Blacklisted module names that are already imported.
    """

    modules: Tuple[str]

    def __init__(self, *modules: str):
        if not modules:
            raise ValueError(f"At least one argument is required")
        self.modules = modules

    def __str__(self):
        return f"Blacklisted modules are already imported: {', '.join(map(repr, self.modules))}"
