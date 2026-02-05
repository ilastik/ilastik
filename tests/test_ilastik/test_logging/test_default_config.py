import re
from pathlib import Path
from typing import List

import pytest

from ilastik.ilastik_logging.default_config import (
    DEFAULT_LOG_NAME,
    KEEP_SESSION_LOGS,
    SESSION_LOGFILE_NAME_PATTERN,
    _delete_old_session_logs,
)


@pytest.fixture
def session_logs(tmp_path) -> List[Path]:
    def create_log_file(i: int) -> Path:
        file_path = tmp_path / f"log_{i:08}_{i:06}.txt"
        assert re.match(SESSION_LOGFILE_NAME_PATTERN, file_path.name)
        file_path.touch()
        return file_path

    n_files = KEEP_SESSION_LOGS + 3
    paths = [create_log_file(i) for i in range(n_files)]
    return paths


def test_delete_old_session_logs(tmp_path, session_logs):
    default_log = tmp_path / DEFAULT_LOG_NAME
    non_log_file = tmp_path / "not_a_logfile.png"
    default_log.touch()
    non_log_file.touch()
    expected_remaining_files = sorted(session_logs[-KEEP_SESSION_LOGS:] + [default_log, non_log_file])

    _delete_old_session_logs(log_dir=tmp_path)
    remaining_files = sorted(tmp_path.iterdir())
    assert remaining_files == expected_remaining_files
