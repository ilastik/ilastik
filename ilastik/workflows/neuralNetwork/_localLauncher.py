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
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from typing import List, Optional

import grpc
import psutil
from tiktorch.proto.inference_pb2 import Empty
from tiktorch.proto.inference_pb2_grpc import FlightControlStub

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
        self._conn_data = None

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
                self._conn_data = json.load(conn_file)

                return f"{self._conn_data['addr']}:{self._conn_data['port']}"

    def stop(self):
        logger.info("stopping local tiktorch instance")
        if not self._process:
            raise RuntimeError(f"Local server is not running")

        chan = grpc.insecure_channel(f"{self._conn_data['addr']}:{self._conn_data['port']}")
        client = FlightControlStub(chan)
        client.Shutdown(Empty())

        if self._process:
            try:
                pid = self._process.pid
                self._process.wait(timeout=2)
            except Exception as e:
                print(e)
            finally:
                # cleanup leaking child processes
                def on_terminate(proc):
                    print("process {} terminated with exit code {}".format(proc, proc.returncode))

                try:
                    process = psutil.Process(pid)
                except psutil.NoSuchProcess:
                    # process can terminate anytime
                    return
                procs = process.children(recursive=True)
                for p in procs:
                    p.terminate()
                gone, alive = psutil.wait_procs(procs, timeout=3, callback=on_terminate)
                for p in alive:
                    p.kill()
                process.kill()
