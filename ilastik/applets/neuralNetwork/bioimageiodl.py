import pathlib
from io import BytesIO
from zipfile import ZIP_DEFLATED

from bioimageio.core import load_raw_resource_description
from bioimageio.core.resource_io.io_ import make_zip
from bioimageio.spec import get_resource_package_content
from bioimageio.spec.shared import resolve_source, raw_nodes, DownloadCancelled
from PyQt5.QtCore import QThread, pyqtSignal
from tqdm.auto import tqdm as std_tqdm

from functools import partial
import logging

logger = logging.getLogger(__file__)

BIOIMAGEIO_WEIGHTS_PRIORITY = ["torchscript", "pytorch_state_dict", "tensorflow_saved_model_bundle"]


class TqdmExt(std_tqdm):
    def __init__(self, *args, callback=None, cancellation_token=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._cb = callback
        self._cancellation_token = cancellation_token

    def update(self, n=1):
        if self._cancellation_token and self._cancellation_token.cancelled:
            raise DownloadCancelled()

        displayed = super().update(n)
        if displayed and self._cb:
            self._cb(**self.format_dict)
        return displayed


class BioImageDownloader(QThread):
    error = pyqtSignal(Exception)
    progress0 = pyqtSignal(int)
    currentUri = pyqtSignal(str)
    progress1 = pyqtSignal(int)
    dataAvailable = pyqtSignal(bytes)

    def __init__(self, model_uri, cancellation_token, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._model_uri = model_uri
        self._exception = None
        self._aborted = False
        self._cancellation_token = cancellation_token

    def run(self):
        try:
            logger.debug(f"Downloading model from {self._model_uri}")
            raw_rd = load_raw_resource_description(self._model_uri)
            package_content = get_resource_package_content(raw_rd, weights_priority_order=BIOIMAGEIO_WEIGHTS_PRIORITY)

            local_package_content = {}
            for k, v in TqdmExt(
                package_content.items(),
                callback=lambda n, total, **kwargs: self.progress0.emit(int(n / total * 100)),
                cancellation_token=self._cancellation_token,
            ):
                if isinstance(v, raw_nodes.URI):
                    self.currentUri.emit(str(v.path))
                    v = resolve_source(
                        v,
                        raw_rd.root_path,
                        pbar=partial(
                            TqdmExt,
                            callback=lambda n, total, **kwargs: self.progress1.emit(int(n / total * 100)),
                            cancellation_token=self._cancellation_token,
                        ),
                    )
                elif isinstance(v, pathlib.Path):
                    v = raw_rd.root_path / v

                local_package_content[k] = v

            with BytesIO() as package_file:
                make_zip(package_file, local_package_content, compression=ZIP_DEFLATED, compression_level=1)
                model_bytes = package_file.getvalue()

            self.dataAvailable.emit(model_bytes)
        except DownloadCancelled:
            return
        except Exception as e:
            self.error.emit(e)
