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
#           http://ilastik.org/license.html
###############################################################################
from ilastik.utility.commands import *

class CommandProcessor(object):
    """
    This class handles incoming commands from inter-process communication (currently
    implemented as a TCP server in ilastik.shell.gui.messageServer). The list of
    allowed commands as well as their implementation can be found in 
    ilastik.utility.commands and extended as needed.
    """
    def __init__(self, shell):
        self.shell = shell
    
    def execute(self, cmd, data):
        if cmd not in allowedCommands:
            raise Exception("Command '%s' not supported" % cmd)
        # if command is implemented, try to execute it with the received data
        try:            
            allowedCommands[cmd](self.shell, data)
        except Exception, e:
            raise Exception("Executing command '%s' failed: %s" % (cmd, e))