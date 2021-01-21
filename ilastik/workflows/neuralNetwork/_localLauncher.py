import logging
import sys
import json
import time
import os
import subprocess
import tempfile

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
    _executable_path: str
    _process: subprocess.Popen

    def __init__(self, executable_path: str) -> None:
        self._executable_path = executable_path
        self._process = None

    def start(self):
        if self._process:
            raise RuntimeError(f"Local server is already running (pid:{self._process.pid})")

        logger.info("Starting local TikTorchServer")

        with tempfile.TemporaryDirectory(prefix="tiktorch_connection") as conn_dir:
            conn_param_path = os.path.join(conn_dir, "conn.json")
            cmd = [self._executable_path, "--port", "0", "--addr", "127.0.0.1", "--connection_file", conn_param_path]

            self._process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
            wait(lambda: os.path.exists(conn_param_path), max_wait=5)

            with open(conn_param_path, "r") as conn_file:
                conn_data = json.load(conn_file)
                return conn_data["addr"], conn_data["port"]

    def stop(self):
        if not self._process:
            raise RuntimeError(f"Local server is not running")

        self._process.terminate()
