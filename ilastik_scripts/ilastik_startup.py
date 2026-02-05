import ctypes.util
import logging
import os
import pathlib
import platform
import shlex
import ssl
import sys
import warnings
from typing import Iterable, Mapping, Sequence, Tuple, Union

logger = logging.getLogger(__name__)


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
        # this is only used in the windows binary - there python.exe is
        # directly in ilastik_root
        if platform.system() == "Windows":
            ilastik_root = pathlib.Path(sys.executable).parent
            assert (ilastik_root / "ilastik.exe").exists()
            _clean_paths(ilastik_root)
        else:
            warnings.warn(
                "--clean_paths argument only supported on windows and should only be used in the binary distribution. Skipping path cleanup."
            )

    # Allow to start-up by double-clicking a project file.
    if len(sys.argv) == 2 and sys.argv[1].endswith(".ilp"):
        sys.argv.insert(1, "--project")

    arg_opts, env_vars = _parse_internal_config("internal-startup-options.cfg")
    sys.argv[1:1] = arg_opts
    os.environ.update(env_vars)


def fix_macos() -> None:
    if platform.system() != "Darwin":
        return
    mac_ver = tuple(map(int, platform.mac_ver()[0].split(".")))
    python_ver = tuple(map(int, platform.python_version().split(".")))
    if mac_ver < (10, 16) or python_ver > (3, 8, 11):
        return

    # https://bugreports.qt.io/browse/QTBUG-87014
    os.environ["QT_MAC_WANTS_LAYER"] = "1"
    os.environ["VOLUMINA_SHOW_3D_WIDGET"] = "0"

    # https://github.com/PixarAnimationStudios/USD/issues/1372#issuecomment-823226088

    real_find_library = ctypes.util.find_library

    def find_library(name):
        if name in ("OpenGL", "GLUT"):
            return f"/System/Library/Frameworks/{name}.framework/{name}"
        return real_find_library(name)

    ctypes.util.find_library = find_library


def fix_ssl() -> None:
    """
    Paths to the CA certificates file and the CA certificates dir are hard-coded into openssl
    during the build process of our installer packages.
    It has some special logic for Windows, and there the paths don't seem to be an issue.
    On Linux and macOS, the build machine's path is written (/opt/conda/envs/ilastik-release/ssl/),
    which does not exist on the end user's machine.
    Being unable to find the cert files means aiohttp cannot connect via https. Currently only
    zarr.storage.FSStore depends on this.
    We override the broken paths using the env vars that openssl listens to. Better would be if we can
    find a way to write the correct paths during build.
    Priority order:
    1) User choice: If already set, leave existing SSL_CERT_FILE or SSL_CERT_DIR untouched
    2) User machine config: Default system locations
    3) Reasonable default: cacert.pem provided by certifi
    4) Last resort: ssl dir inside the ilastik package
        (macOS: $app_root/Contents/ilastik-release/ssl, Linux: $tar_root/ssl)
    """
    if platform.system() == "Windows":
        return

    ssl_paths = ssl.get_default_verify_paths()
    if os.path.isfile(ssl_paths.openssl_cafile) or "SSL_CERT_FILE" in os.environ or "SSL_CERT_DIR" in os.environ:
        # All good, or user has manually set an env variable (one of SSL_CERT_FILE or SSL_CERT_DIR is sufficient)
        return

    # Check default locations first so that we preferably use the system certs if available
    # https://serverfault.com/a/722646
    default_cert_files = (
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
        "/etc/ssl/ca-bundle.pem",
        "/etc/pki/tls/cacert.pem",
        "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem",
        "/etc/ssl/cert.pem",
    )
    for cert_file in default_cert_files:
        if os.path.isfile(cert_file):
            logger.info(f"Found cert file in {cert_file}, writing to env var SSL_CERT_FILE")
            os.environ["SSL_CERT_FILE"] = cert_file
            return

    default_cert_paths = (
        "/etc/ssl/certs",
        "/system/etc/security/cacerts",
        "/usr/local/share/certs",
        "/etc/pki/tls/certs",
        "/etc/openssl/certs",
        "/var/ssl/certs",
    )
    for certs_dir in default_cert_paths:
        if os.path.isdir(certs_dir):
            logger.info(f"Found certs dir at {certs_dir}, writing to env var SSL_CERT_DIR")
            os.environ["SSL_CERT_DIR"] = certs_dir
            return

    # Try certifi
    import certifi

    if os.path.isfile(certifi.where()):
        logger.info(f"Falling back to certifi for SSL at {certifi.where()}, writing to env var SSL_CERT_FILE")
        os.environ["SSL_CERT_FILE"] = certifi.where()
        return

    # None of the defaults worked, we have to find the ssl dir inside the ilastik package.
    # This can be tricky, because the path to the package root isn't stored anywhere.
    # We check __file__'s parents, because we know that this script is in the package.
    # On Linux, that easily gets us to $tar_root/ssl.
    # On macOS, we need $app_root/Contents/ilastik-release/ssl.
    # This script file should also be somewhere inside ilastik-release.
    for candidate_dir in pathlib.Path(__file__).parents:
        package_cert_file = candidate_dir / "ssl" / "cert.pem"
        if package_cert_file.is_file():
            logger.info(f"Found cert file in {str(package_cert_file)}, writing to env var SSL_CERT_FILE")
            os.environ["SSL_CERT_FILE"] = str(package_cert_file)
            return

        package_cert_dir = candidate_dir / "ssl" / "certs"
        if package_cert_file.is_dir():
            logger.info(f"Found certs dir at {str(package_cert_dir)}, writing to env var SSL_CERT_DIR")
            os.environ["SSL_CERT_DIR"] = str(package_cert_dir)
            return

    logger.warning(
        "Could not find SSL CA certificates directory or file. "
        "This means connecting to web servers via https may not be possible. "
        "If you know the path to the CA certificates on your machine, you can set the environment "
        "variables SSL_CERT_FILE or SSL_CERT_DIR."
    )


def main():
    path_setup()
    fix_macos()
    fix_ssl()

    from ilastik.__main__ import main

    main()


if __name__ == "__main__":
    main()
