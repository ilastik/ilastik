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
from ilastik.utility.commandProcessor import CommandProcessor

import SocketServer
import threading
import socket
import logging
import json
import atexit

logger = logging.getLogger(__name__)

class TCPServerBoundToShell(SocketServer.TCPServer):
    """
    SocketServer.TCPServer which is linked to the ilastik shell
    """
    def __init__(self, server_address, RequestHandlerClass, shell=None, bind_and_activate=True):
        self.shell = shell
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)

class MessageServer(object):
    """
    This TCP message server manages both client and server connections. It allows ilastik to 
    listen on a predefined host/port and send messages to an arbitrary number of clients 
    registered beforehand. Functions relevant to users are:
    - setupServer(host, port, startListening): Establish server listening to incoming messages
    - connect(host, port, name): Add client 'name' to the outgoing connections
    - send(name, data): Send a data package (python dict) to the client 'name'
    """
    connections = {}
    server = None
    
    def __init__(self, parent, host=None, port=None, startListening=True):
        self.parent = parent
        
        if not host is None and not port is None:
            self.setupServer(host, port, startListening)
            
    def setupServer(self, host, port, startListening=True):
        try:
            self.host = host
            self.port = port
            self._setupServer()
            if startListening:
                self._startListening()
        except Exception, e:
            logger.error('Failed to set up MessageServer: %s' % e)    
    
    def connect(self, host, port, name):
        try:
            # send handshake message to check if connection possible
            # -> establish connection only while sending a message
            handshake = {'command': 'handshake', 'name': 'ilastik',
                         'host': self.host, 'port': self.port}
            self._send(host, port, data=handshake)
            self.connections[name] = {'host': host, 'port': port}
            logger.info("Successfully connected to server '%s' at %s:%d" % (name, host, port))
        except Exception, e:
            if name in self.connections:
                del self.connections[name]
            logger.error("Error connecting to server '%s': %s" % (name, e))
            
    def send(self, name, data):
        try:
            if name in self.connections:
                self._send(self.connections[name]['host'], 
                           self.connections[name]['port'], 
                           data)
                logger.info("Sent message to '%s': %s" % (name, data))
            else:
                raise Exception("No connection with name '%s' exists" % name)
        except Exception, e:
            logger.error("Error sending message '%s' to '%s': %s" % (data, name, e))
    
    def _send(self, host, port, data=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((host, port))
            sock.send(json.dumps(data))
        except Exception, e:
            raise Exception('%s', e)
        finally:
            sock.close()
            
    def _setupServer(self):
        self.server = TCPServerBoundToShell((self.host, self.port), TCPRequestHandler, shell=self.parent)
        self.thread = threading.Thread(name="IlastikTCPServer", target=self.server.serve_forever)
        self.thread.daemon = True
        
    def _startListening(self): 
        try:
            if not self.server is None:
                self.thread.start()
                atexit.register( self.server.shutdown )
            else:
                raise Exception('TCP Server not set up yet')
        except:
            # not listening
            pass

    def connected(self, name):
        return (name in self.connections)
    
    def closeConnection(self, name):
        if name in self.connections:
            del self.connections[name]
    
    def closeConnections(self):
        for name in self.connections:
            self.closeConnection(name)
    
    def __del__(self):
        self.closeConnections()
        self.thread.__stop()    

class TCPRequestHandler(SocketServer.StreamRequestHandler):
    """
    StreamRequestHandler for incoming socket streams which checks if the incoming
    data is in proper format for ilastik to handle (python dict in json format with
    a field named 'command') and propagates it to the CommandProcessor.
    """
    def __init__(self, request, client_address, server):
        self.CommandProcessor = CommandProcessor(shell=server.shell)
        SocketServer.StreamRequestHandler.__init__(self, request, client_address, server)
    
    def handle(self):
        data = json.loads(self.rfile.readline().strip())
        logger.info("Received message from %s: %s" % (self.client_address, data))
        try:
            self.parse(data)
        except Exception, e:
            logger.warn("Received TCP message could not be parsed: %s" % e)
            
        self.respond(data)
    
    def parse(self, data):
        # check if data is in correct format
        if not isinstance(data, dict):
            raise Exception("Message is not a proper JSON object")
        
        # transform all keys to lower case
        data = dict((k.lower(), v) for k,v in data.iteritems())
        
        # abort parsing if keyword 'command' is missing
        if not 'command' in data:
            raise Exception("Missing keyword 'command'")
        
        # hand data to a command processor (the commands are defined in
        # ilastik/utility/commands.py)
        self.CommandProcessor.execute(data['command'], data)
            
    def respond(self, data):
        pass