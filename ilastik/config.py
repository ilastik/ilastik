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
#		   http://ilastik.org/license.html
###############################################################################
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

[lazyflow]
threads: -1
total_ram_mb: 0
"""

cfg = ConfigParser.SafeConfigParser()
def init_ilastik_config( userConfig=None ):
    global cfg
    cfg.readfp(io.BytesIO(default_config))

    if userConfig is not None and not os.path.exists(userConfig):
        raise Exception("ilastik config file does not exist: {}".format( userConfig ))

    if userConfig is None:    
        userConfig = os.path.expanduser("~/.ilastikrc")
    if os.path.exists(userConfig):
        cfg.read(userConfig)

init_ilastik_config()