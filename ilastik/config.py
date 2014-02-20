# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

import ConfigParser
import io, os

"""
ilastik will read settings from ~/.ilastikrc

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
"""

cfg = ConfigParser.SafeConfigParser()
cfg.readfp(io.BytesIO(default_config))
userConfig = os.path.expanduser("~/.ilastikrc")
if os.path.exists(userConfig):
    cfg.read(userConfig)