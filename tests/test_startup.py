import os
import platform
import ssl

from ilastik_scripts.ilastik_startup import fix_ssl


def test_startup_ssl_paths():
    """
    The point of this test is to ensure that correct paths to SSL certs are available during runtime.
    The problem of broken paths only exists in the packaged ilastik installers/bundles though,
    so this test is effectively useless unless we run it on the installed packages.
    Leaving it as a reminder that we should be running tests on the packages after build,
    and as additional documentation for why fix_ssl exists.
    """
    fix_ssl()
    WIN = platform.system() == "Windows"  # On Windows the cert file/folder don't seem to be needed
    default_file_exists = os.path.isfile(ssl.get_default_verify_paths().openssl_cafile)
    override_file_exists = os.path.isfile(os.environ.get("SSL_CERT_FILE", ""))
    assert WIN or default_file_exists or override_file_exists
