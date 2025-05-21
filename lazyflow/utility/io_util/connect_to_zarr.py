import logging
import os
from typing import Optional
from urllib.parse import unquote_to_bytes

import s3fs
from aiohttp import ClientResponseError, ClientConnectorError
from botocore.exceptions import NoCredentialsError, EndpointConnectionError
from zarr.storage import FSStore


logger = logging.getLogger(__name__)


def _try_authenticated_aws_s3(uri, kwargs, mode, test_path) -> Optional[FSStore]:
    authenticated_store = FSStore(uri, mode=mode, anon=False, **kwargs)
    try:
        logger.debug(f"Trying to access path={test_path} at uri={uri} with S3FS credentials.")
        _ = authenticated_store[test_path]
    except NoCredentialsError:
        logger.warning(
            "AWS S3 credentials are not set up. Will continue without authentication and assume "
            "the bucket is public.\n"
            "If this bucket may be private, please check your credentials are set up for S3FS."
        )
    except EndpointConnectionError as ece:
        if "169.254.169.254" in str(ece):
            pass  # Happens when s3fs tries and fails token authentication, no need to feed back to user
    except KeyError as ke:
        if isinstance(ke.__context__.__context__, FileNotFoundError):
            # Even if .zattrs isn't here, we still managed to access the bucket
            logger.warning(
                "S3 credentials found, continuing with authentication. "
                "This may prevent access if the dataset is actually public."
            )
            return authenticated_store
    else:
        logger.info("Successfully authenticated with S3.")
        return authenticated_store
    logger.info("Tried to authenticate with S3FS credentials but failed. Continuing without authentication.")
    return None


def _try_authenticated_s3_compatible(uri, kwargs, e, test_path) -> FSStore:
    split_bucket = uri.split("/", 4)
    if len(split_bucket) < 5:  # Does not follow S3 pattern (https://s3.server.org/bucket/file)
        raise ConnectionError(
            f"Server refused permission to read {uri}.\n"
            "It seems authentication is required, but ilastik does not support this kind of server yet."
        ) from e
    base_uri_inc_bucket = "/".join(split_bucket[:4])
    sub_uri = split_bucket[4]
    fs = s3fs.S3FileSystem(anon=False, endpoint_url=base_uri_inc_bucket)
    store = FSStore(sub_uri, fs=fs, **kwargs)
    try:
        logger.debug(f"Trying path={sub_uri}/{test_path} in bucket={base_uri_inc_bucket} with S3FS credentials.")
        _ = store[test_path]
    except (KeyError, NoCredentialsError) as ee:
        if isinstance(ee.__context__, PermissionError) or isinstance(ee, NoCredentialsError):
            # This probably is an S3-compatible store, but auth rejected/not found.
            raise ConnectionError(
                f"Server refused permission to read {uri}.\n"
                f"Please ensure you have access to this bucket and your credentials are set up for S3FS."
            ) from ee
    logger.info(
        "Server requires authentication and seems to have accepted S3FS credentials. Continuing with authenticated store."
    )
    return store


def ensure_connection_and_get_store(uri: str, mode="r", **kwargs) -> FSStore:
    test_path = ".zattrs"
    if uri.startswith("file:"):
        # Zarr's FSStore implementation doesn't unescape file URLs before piping them to
        # the file system. We do it here the same way as in pathHelpers.uri_to_Path.
        # Primarily this is to deal with spaces in Windows paths (encoded as %20).
        uri = os.fsdecode(unquote_to_bytes(uri))
    if uri.startswith("s3:"):
        # s3fs.S3FileSystem defaults to anon=False, but we want to try anon=True first
        store = FSStore(uri, anon=True, mode=mode, **kwargs)
    else:
        # Non-S3 don't like to be called with anon keyword
        store = FSStore(uri, mode=mode, **kwargs)
    try:
        store[test_path]
        # Any error not handled here is either a successful connection (even 404), or an unknown problem
    except (KeyError, ClientResponseError) as e:
        # FSStore wraps some errors in KeyError (FileNotFoundError even double-wrapped)
        if isinstance(e.__context__, ClientConnectorError):
            raise ConnectionError(f"Could not connect to {e.__context__.host}:{e.__context__.port}.") from e
        if isinstance(e.__context__, PermissionError) and uri.startswith("s3:"):
            # Depending on bucket setup, AWS S3 may respond with "PermissionError: Access Denied"
            # even if the bucket is public (but the .zattrs file is not at this URI).
            # So test if authentication is set up, but continue with the unauthenticated store if not.
            authenticated_store = _try_authenticated_aws_s3(uri, kwargs, mode, test_path)
            if authenticated_store is not None:
                store = authenticated_store
        if isinstance(e, ClientResponseError) and e.status == 403:
            # Server requires authentication. Try if it's an S3-compatible store.
            store = _try_authenticated_s3_compatible(uri, kwargs, e, test_path)
    return store
