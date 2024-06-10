import os
import platform
import pytest

from ilastik.applets.dataSelection import multiscaleDatasetBrowser

WIN = platform.system() == "Windows"


@pytest.mark.parametrize(
    "text_input,expected",
    [
        ("https://example.com/data.zarr", "https://example.com/data.zarr"),
        ("precomputed://https://example.com", "precomputed://https://example.com"),
        ("https://example.com/p?q%20#a", "https://example.com/p?q%20#a"),
    ],
)
def test_validate_uri(text_input, expected):
    assert multiscaleDatasetBrowser._validate_uri(text_input) == expected


@pytest.mark.parametrize(
    "invalid_input",
    [
        "",
        "example.com",  # Missing protocol
    ],
)
def test_validate_uri_raises(invalid_input):
    with pytest.raises(ValueError):
        multiscaleDatasetBrowser._validate_uri(invalid_input)


@pytest.mark.skipif(WIN, reason="Can't test unix paths on Windows")
@pytest.mark.parametrize(
    "text_input,expected",
    [
        ("/", "file:///"),
        ("file:///home/", "file:///home/"),
        # Actually malformed (missing empty host). Maps to //home/, which
        # "may be interpreted in an implementation-defined manner".
        # Seems to correctly resolve to /home/ on common systems though.
        ("file://home/", "file://home/"),
    ],
)
def test_validate_uri_from_posix_path(text_input, expected):
    assert multiscaleDatasetBrowser._validate_uri(text_input) == expected


@pytest.mark.skipif(WIN, reason="Can't test unix paths on Windows")
@pytest.mark.parametrize(
    "invalid_input",
    [
        "/gibberish_123/",  # Path does not exist
    ],
)
def test_validate_uri_from_posix_path_raises(invalid_input):
    with pytest.raises(ValueError):
        multiscaleDatasetBrowser._validate_uri(invalid_input)


@pytest.mark.skipif(not WIN, reason="Windows paths can only be tested on Windows")
@pytest.mark.parametrize(
    "text_input,expected",
    [
        ("C:\\", "file:///C:/"),
        ("C:/", "file:///C:/"),
        ("file:///C:\\", "file:///C:\\"),  # User manually added protocol
        ("file:///C:/", "file:///C:/"),
    ],
)
def test_validate_uri_from_Windows_path(text_input, expected):
    assert multiscaleDatasetBrowser._validate_uri(text_input) == expected


@pytest.mark.skipif(not WIN, reason="Windows paths can only be tested on Windows")
@pytest.mark.parametrize(
    "dir_name",
    [
        "dirname with space",
        "dirname%20with%percent",
    ],
)
def test_validate_uri_from_existing_Windows_path_with_special_characters(tmp_path, dir_name):
    full_path = tmp_path / dir_name
    os.mkdir(full_path)
    text_input = str(full_path)
    expected = full_path.as_uri()
    try:
        assert multiscaleDatasetBrowser._validate_uri(text_input) == expected
    finally:
        os.rmdir(full_path)


@pytest.mark.skipif(not WIN, reason="Windows paths can only be tested on Windows")
@pytest.mark.parametrize(
    "invalid_input",
    [
        "C:\\gibberish_123",  # Path does not exist
        "file:///C:\\gibberish_123",  # Path does not exist
        "file://C:\\",  # Missing empty host
    ],
)
def test_validate_uri_from_Windows_path_raises(invalid_input):
    with pytest.raises(ValueError):
        multiscaleDatasetBrowser._validate_uri(invalid_input)
