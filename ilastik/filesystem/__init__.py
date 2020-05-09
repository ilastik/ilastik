from .HttpPyFs import HttpPyFs

from urllib.parse import urlparse
from fs.base import FS
from fs.osfs import OSFS
from typing import Tuple
from pathlib import Path

def get_filesystem_for(url: str) -> Tuple[FS, Path]:
    single_protocol_url = "://".join(url.split("://")[-2:])
    parsed = urlparse(single_protocol_url)
    path = Path(parsed.path)
    if parsed.scheme in ("http", "https"):
        http_fs_url = parsed.scheme + "://" + parsed.netloc
        return HttpPyFs(http_fs_url), path
    elif parsed.scheme in ("", "file"):
        return OSFS(Path(parsed.path).anchor), path
    raise ValueError(f"Don't know how to open filesystem for {url}")
