###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2021, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
import logging
import sys
import json
import time
import os
import subprocess
import tempfile
from typing import Optional, List

logger = logging.getLogger(__name__)


def wait(done, interval=0.1, max_wait=1):
    start = time.time()

    while True:
        if done():
            break

        passed = time.time() - start

        if passed > max_wait:
            raise RuntimeError("timeout")
        else:
            time.sleep(interval)


class LocalServerLauncher:
    _executable_path: List[str]
    _process: Optional[subprocess.Popen]

    def __init__(self, executable_path: List[str]) -> None:
        self._executable_path = executable_path
        self._process = None

    def start(self):
        if self._process:
            raise RuntimeError(f"Local server is already running (pid:{self._process.pid})")

        logger.info("Starting local TikTorchServer")

        with tempfile.TemporaryDirectory(prefix="tiktorch_connection") as conn_dir:
            conn_param_path = os.path.join(conn_dir, "conn.json")
            cmd = self._executable_path + ["--port", "0", "--addr", "127.0.0.1", "--connection-file", conn_param_path]

            self._process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
            try:
                wait(lambda: os.path.exists(conn_param_path), max_wait=20)
            except RuntimeError:
                self.stop()

            with open(conn_param_path, "r") as conn_file:
                conn_data = json.load(conn_file)
                return f"{conn_data['addr']}:{conn_data['port']}"

    def stop(self):
        logger.info("stopping local tiktorch instance")
        if not self._process:
            raise RuntimeError(f"Local server is not running")

        self._process.terminate()
