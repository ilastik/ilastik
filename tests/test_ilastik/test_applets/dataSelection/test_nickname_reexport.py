from ilastik.applets.dataSelection import opDataSelection
from ilastik.applets.dataSelection import url_nickname


def test_nickname_reexport_matches_canonical():
    """Smoke test: ensure the re-export in opDataSelection delegates to the canonical helper.

    This guards against accidental divergence between the public symbol and the
    canonical implementation.
    """
    sample_uris = [
        "file:///C:/Users/me/container.zarr/multiscale",
        "s3://bucket/container.n5/dset",
        "file:///tmp/container.h5::/group/dset",
    ]

    for uri in sample_uris:
        assert opDataSelection.nickname_from_url(uri) == url_nickname.nickname_from_url(uri)
