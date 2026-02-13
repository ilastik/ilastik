import io
from typing import Any, Callable, Dict

from qtpy.QtCore import QThread, Signal
from bioimageio.spec import ValidationContext, get_resource_package_content
from tqdm.auto import tqdm as std_tqdm
import logging

logger = logging.getLogger(__file__)

BIOIMAGEIO_WEIGHTS_PRIORITY = ("torchscript", "pytorch_state_dict")


class DownloadCancelled(Exception):
    pass


class TqdmExt(std_tqdm):
    def __init__(self, *args, callback=None, cancellation_token=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._cb = callback
        self._cancellation_token = cancellation_token

    def update(self, n=1):
        if self._cancellation_token and self._cancellation_token.cancelled:
            # Note: bioimageio imports are delayed as to prevent https request to
            # github and bioimage.io on ilastik startup

            raise DownloadCancelled()

        displayed = super().update(n)
        if displayed and self._cb:
            self._cb(**self.format_dict)
        return displayed


class BioImageDownloader(QThread):
    error = Signal(Exception)
    progress0 = Signal(int)
    currentUri = Signal(str)
    progress1 = Signal(int)
    dataAvailable = Signal(bytes)

    def __init__(self, model_uri, cancellation_token, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._model_uri = model_uri
        self._exception = None
        self._aborted = False
        self._cancellation_token = cancellation_token

    def run(self):
        try:
            # Note: bioimageio imports are delayed as to prevent https request to
            # github and bioimage.io on ilastik startup
            from bioimageio.spec import load_description, save_bioimageio_package_to_stream
            from bioimageio.spec.common import HttpUrl
            from bioimageio.spec._internal.io import download

            logger.debug(f"Downloading model from {self._model_uri}")
            rd = load_description(self._model_uri, format_version="latest", perform_io_checks=False)

            with ValidationContext(perform_io_checks=False):
                package_content = get_resource_package_content(rd, weights_priority_order=BIOIMAGEIO_WEIGHTS_PRIORITY)

            def _callback(progress_signal: Signal) -> Callable[[int, int], None]:
                def _cb(n: int, total: int, **kwargs):
                    if total > 0:
                        progress_signal.emit(int(n / total * 100))

                return _cb

            for k, v in TqdmExt(
                package_content.items(),
                callback=_callback(self.progress0),
                cancellation_token=self._cancellation_token,
            ):
                if isinstance(v, HttpUrl):
                    assert v.path
                    self.currentUri.emit(v.path.split("/")[-1])
                    download(
                        v,
                        progressbar=TqdmExt(
                            total=1,  # hack: it will be set later by HTTPDownloader, but it is needed for a valid tqdm
                            callback=_callback(self.progress1),
                            cancellation_token=self._cancellation_token,
                        ),
                    )

            # this can take time, use a progress dialog or a busy cursor
            model_binary = io.BytesIO()
            save_bioimageio_package_to_stream(rd, output_stream=model_binary)

            self.dataAvailable.emit(model_binary.getvalue())
        except DownloadCancelled:
            return
        except Exception as e:
            self.error.emit(e)
