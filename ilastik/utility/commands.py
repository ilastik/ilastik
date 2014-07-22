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
"""
Define a function for each message ilastik should be able to process:
def myAction(shell, data)
"""
def setViewerPos(shell, data):
    # data is a dict which may contain one entry for each coordinate
    pos5d = []
    for l in 'txyzc':
        if l in data:
            pos5d.append(data[l])
        else:
            pos5d.append(0)
    shell.setAllViewersPosition(pos5d)
        
def connectToServer(shell, data):
    if ('port' in data and 'name' in data and 
        isinstance(data['port'], int) and 
        isinstance(data['name'], basestring)):
        if 'host' in data:
            host = data['host']
        else:
            host = 'localhost'
        name = data['name'].encode('ascii','ignore')
        shell.socketServer.connect(host, data['port'], name)
        shell.newServerConnected(name)
    else:
        raise Exception("Please supply at least server 'name' and 'port' for handshake")

"""
 Link command names to function names
"""
allowedCommands = {'setviewerposition': setViewerPos,
                   'handshake': connectToServer}