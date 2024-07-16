import os
import platform
import ssl

from ilastik_scripts.ilastik_startup import fix_ssl


def test_startup_ssl_paths():
    fix_ssl()
    WIN = platform.system() == "Windows"  # On Windows the cert file/folder don't seem to be needed
    default_file = ssl.get_default_verify_paths().openssl_cafile
    fixed_file = os.environ.get("SSL_CERT_FILE", "")
    assert WIN or os.path.isfile(default_file) or os.path.isfile(fixed_file)
