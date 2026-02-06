import importlib
import importlib.util
from pathlib import Path

import pytest


def _load_nickname_helper():
    """Try importing the package helper; if that fails (missing heavy deps locally)
    load the module directly from the file path so tests remain runnable locally.
    """
    try:
        # Prefer the installed/package import (used in CI)
        from ilastik.applets.dataSelection.url_nickname import nickname_from_url

        return nickname_from_url
    except Exception:
        # Fallback: load by path relative to repo layout
        repo_root = Path(__file__).parents[4]
        helper_path = repo_root / "ilastik" / "applets" / "dataSelection" / "url_nickname.py"
        spec = importlib.util.spec_from_file_location("url_nickname", str(helper_path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.nickname_from_url


nickname_from_url = _load_nickname_helper()


@pytest.mark.parametrize(
    "uri,nickname",
    [
        ("file:///C:/Users/me/multiscale.zarr", "multiscale"),
        ("file:///C:/Users/me/multiscale.zarr/", "multiscale"),
        ("file:///C:/Users/me/multiscale.ome.zarr", "multiscale"),
        ("file:///C:/Users/me/container.zarr/multiscale", "container-multiscale"),
        ("file:///C:/Users/me/container.zarr/multiscale/", "container-multiscale"),
        ("file:///C:/Users/me/container.ome.zarr/multiscale", "container-multiscale"),
        ("file:///C:/Users/me/container.zarr/multiscale.zarr", "multiscale"),
        ("file:///C:/Users/me/container.zarr/multiscale.ome.zarr", "multiscale"),
        ("file:///C:/Users/me/multiscale.zarr/scale1", "multiscale-scale1"),
        ("file:///C:/Users/me/multiscale.ome.zarr/scale1", "multiscale-scale1"),
        ("file:///C:/Users/me/container.zarr/multiscale/scale1", "container-multiscale-scale1"),
        ("file:///C:/Users/me/container.ome.zarr/multiscale/scale1", "container-multiscale-scale1"),
        ("file:///C:/Users/me/container.zarr/multiscale.zarr/scale1", "multiscale-scale1"),
        ("file:///C:/Users/me/container.zarr/multiscale.ome.zarr/scale1", "multiscale-scale1"),
        ("https://some.example.org/s3/multiscale.zarr", "multiscale"),
        ("https://some.example.org/s3/multiscale.zarr/", "multiscale"),
        ("https://some.example.org/s3/multiscale.ome.zarr", "multiscale"),
        ("https://some.example.org/s3/container.zarr/multiscale", "container-multiscale"),
        ("https://some.example.org/s3/container.zarr/multiscale/", "container-multiscale"),
        ("https://some.example.org/s3/container.ome.zarr/multiscale", "container-multiscale"),
        ("https://some.example.org/s3/container.zarr/multiscale.zarr", "multiscale"),
        ("https://some.example.org/s3/container.zarr/multiscale.ome.zarr", "multiscale"),
        ("https://some.example.org/s3/multiscale.zarr/scale1", "multiscale-scale1"),
        ("https://some.example.org/s3/multiscale.ome.zarr/scale1", "multiscale-scale1"),
        ("https://some.example.org/s3/container.zarr/multiscale/scale1", "container-multiscale-scale1"),
        ("https://some.example.org/s3/container.ome.zarr/multiscale/scale1", "container-multiscale-scale1"),
        ("https://some.example.org/s3/container.zarr/multiscale.zarr/scale1", "multiscale-scale1"),
        ("https://some.example.org/s3/container.zarr/multiscale.ome.zarr/scale1", "multiscale-scale1"),
    ],
)
def test_urldatasetinfo_nickname(uri, nickname):
    assert nickname_from_url(uri) == nickname
