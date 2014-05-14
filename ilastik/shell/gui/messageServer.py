import SocketServer
import threading
import socket
import logging
import string

logger = logging.getLogger(__name__)

class TCPServerBoundToShell(SocketServer.TCPServer):
    def __init__(self, server_address, RequestHandlerClass, shell=None, bind_and_activate=True):
        self.shell = shell
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)

class MessageServer(object):
    connections = {}
    
    def __init__(self, parent, host, port, startListening=True):
        self.parent = parent
        self.host = host
        self.port = port   
        
        if startListening:
            self.setupServer()
            self.startListening()
    
    def __del__(self):
        self.closeConnections()
        self.thread.__stop()
    
    def setupServer(self):
        self.server = TCPServerBoundToShell((self.host, self.port), TCPRequestHandler, shell=self.parent)
        self.thread = threading.Thread(name="IlastikTCPServer", target=self.server.serve_forever)
        
    def startListening(self): 
        try:
            if not self.server is None:
                self.thread.start()
            else:
                raise Exception('TCP Server not set up yet')
        except:
            # not listening
            pass

    def connect(self, host, port, name):
        try:
            self.connections[name] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connections[name].connect((host, port))
        except Exception, e:
            logger.error("Error connecting to socket '%s': %s" % (name, e))
    
    def closeConnection(self, name):
        if name in self.connections:
            try:
                self.connections[name].close()
            except:
                pass
            del self.connections[name]
    
    def closeConnections(self):
        for name in self.connections:
            self.closeConnection(name)
    
    def send(self, name, message):  
        try:
            if name in self.connections:
                self.connections[name].send(message)
            else:
                raise Exception("No connection with name '%s' exists" % name)
        except Exception, e:
            logger.error("Error sending message '%s' to '%s': %s" % (message, name, e))

class TCPRequestHandler(SocketServer.StreamRequestHandler):                 
    def handle(self):
        data = self.rfile.readline().strip()
        logger.info("%s wrote: %s" % (self.client_address[0], data))
        
        split = string.split(data[1:-1],':')
        command = split[0]
        param = split[1]
        
        
        if command == 'jumpToPos':
            pos5d = {'t': 0, 'x': 0, 'y': 0, 'z': 0, 'c': 0}
            coords = string.split(param, ',')
            for coord in coords:
                split = string.split(coord, '=')
                axis = split[0]
                pos = int(split[1])
                if axis in pos5d and isinstance(pos, int):
                    pos5d[axis] = pos
            print pos5d        
        
        print self.server.shell
        if not self.server.shell.workflow is None:
            for app in self.server.shell.workflow.applets:
                try:
                    app._gui.currentGui().editor.posModel.slicingPos = [pos5d['x'],pos5d['y'],pos5d['z']]
                    app._gui.currentGui().editor.posModel.time = [pos5d['t']]
                    app._gui.currentGui().editor.posModel.channel = [pos5d['c']]
                except:
                    pass
                
        """
        editor.posModel.slicingPos = midpos3d
        self.editor.navCtrl.panSlicingViews( midpos3d, [0,1,2] )
        """