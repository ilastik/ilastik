
"""Utilities for dataset nicknames (backwards compatibility).

This module provides a small helper used by older code and tests:
``nickname_from_url``. Newer code should prefer the utilities in
``opDataSelection``; this module remains to avoid breaking imports in
projects and CI while we migrate callers.
"""

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

    Preference rules:
    - If a 'scale<N>' path segment exists, use the segment immediately before it.
    - Otherwise prefer the last path segment that looks like a known container
      (e.g. ends with '.zarr', '.n5', etc.), stripped of that extension.
    - Fallback to the last path segment.
    """
    parsed = urlparse(url)
    path = unquote(parsed.path or "")
    segments = [seg for seg in path.split("/") if seg]

    if not segments:
        return _sanitize_part(parsed.netloc or "unnamed")

    scale_re = re.compile(r"^scale\d+$", re.IGNORECASE)
    candidate: str | None = None

    for i, seg in enumerate(segments):
        if scale_re.match(seg) and i > 0:
            candidate = segments[i - 1]
            break

    if candidate is None:
        for seg in reversed(segments):
            for ext in KNOWN_CONTAINER_EXTS:
                if seg.lower().endswith(ext):
                    candidate = seg[: -len(ext)]
                    break
            if candidate:
                break

    if candidate is None:
        candidate = segments[-1]

    for ext in KNOWN_CONTAINER_EXTS:
        if candidate.lower().endswith(ext):
            candidate = candidate[: -len(ext)]
            break

    nick = _sanitize_part(candidate)
    if not nick:
        return "unnamed"
    if len(nick) > max_len:
        nick = nick[: max_len].rstrip("-_.")
    return nick

