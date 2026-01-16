import pytest

from ilastik.applets.dataSelection.url_nickname import nickname_from_url


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
