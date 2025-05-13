###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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
# 		   http://ilastik.org/license.html
###############################################################################

import configparser
import os
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

import platformdirs

"""
ilastik will read settings from ilastik.ini
which should be located at

* windows: C:\\Users\\<USERNAME>\\AppData\\Local\\ilastik
* osx: /Users/<USERNAME>/Library/Caches/ilastik
* linux: /home/<USERNAME>/.config/ilastik

Example:

[ilastik]
debug: false
plugin_directories: ~/.ilastik/plugins,
logging_config: ~/custom_ilastik_logging_config.json
"""

default_config = """
[ilastik]
debug: false
plugin_directories: ~/.ilastik/plugins,
output_filename_format: {dataset_dir}/{nickname}_{result_type}
output_format: compressed hdf5

[lazyflow]
threads: -1
total_ram_mb: 0
"""


@dataclass
class RuntimeCfg:
    tiktorch_executable: Optional[List[str]] = None
    preferred_cuda_device_id: Optional[str] = None


cfg: configparser.ConfigParser = configparser.ConfigParser()
cfg_path: Optional[Path] = None
runtime_cfg: RuntimeCfg = RuntimeCfg()


def _init(path: Union[None, str, bytes, os.PathLike]) -> None:
    """Initialize module variables."""
    config_path = Path(path) if path is not None else None

    config = configparser.ConfigParser()
    config.read_string(default_config)
    if config_path is not None:
        config.read(config_path)

    global cfg, cfg_path
    cfg, cfg_path = config, config_path


def _get_default_config_path() -> Optional[Path]:
    """Return a default, valid config path, or None if none of the default paths are valid."""
    old = Path.home() / ".ilastikrc"
    new = Path(platformdirs.user_config_dir(appname="ilastik", appauthor=False)) / "ilastik.ini"

    if old.is_file():
        warnings.warn(
            f"ilastik config file location {str(old)!r} is deprecated; "
            f"move config file to the new location {str(new)!r}",
            DeprecationWarning,
        )
        return old
    elif new.is_file():
        return new
    else:
        return None


def init_ilastik_config(path: Union[None, str, bytes, os.PathLike] = None) -> None:
    if path is None:
        _init(_get_default_config_path())
    elif os.path.isfile(path):
        _init(path)
    else:
        raise RuntimeError(f"ilastik config file {path} does not exist or is not a file")


init_ilastik_config()
