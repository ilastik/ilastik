from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urlparse, unquote


KNOWN_CONTAINER_EXTS = (
    ".ome.zarr",
    ".zarr",
    ".n5",
    ".ome.n5",
    ".h5",
    ".hdf5",
    ".ilp",
)


def _sanitize_part(part: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_.-]", "_", part)
    # collapse multiple underscores
    s = re.sub(r"_+", "_", s)
    # remove leading/trailing underscores/dashes/dots
    s = s.strip("_.-")
    return s.lower()


def _find_container_index(segments: Iterable[str]) -> int:
    """Return the index of the last segment that looks like a container (has a known extension).

    If none found, return -1.
    """
    last_idx = -1
    for i, seg in enumerate(segments):
        seg_low = seg.lower()
        for ext in KNOWN_CONTAINER_EXTS:
            if seg_low.endswith(ext):
                last_idx = i
                break
    return last_idx


def nickname_from_url(url: str, max_len: int = 64) -> str:
    """Derive a readable nickname from a URI.

    Pattern: find the last path segment that has a known container extension (e.g. .zarr) and
    use that segment (without extension) plus any following path segments joined by '-'.

    Examples:
      file:///.../container.zarr/multiscale/scale1 -> container-multiscale-scale1
      file:///.../multiscale.zarr -> multiscale
    """
    parsed = urlparse(url)
    path = unquote(parsed.path or "")
    # Split and drop empty segments
    segments = [seg for seg in path.split("/") if seg]

    if not segments:
        return _sanitize_part(parsed.netloc or "unnamed")

    container_idx = _find_container_index(segments)
    if container_idx >= 0:
        parts = segments[container_idx:]
    else:
        # fallback: use the last segment only
        parts = [segments[-1]]

    # strip extensions on the first part if any
    first = parts[0]
    for ext in KNOWN_CONTAINER_EXTS:
        if first.lower().endswith(ext):
            first = first[: -len(ext)]
            break
    sanitized = [_sanitize_part(first)] + [_sanitize_part(p) for p in parts[1:]]
    # drop empty parts
    sanitized = [p for p in sanitized if p]
    if not sanitized:
        return "unnamed"
    nick = "-".join(sanitized)
    if len(nick) > max_len:
        nick = nick[: max_len].rstrip("-_.")
    return nick
