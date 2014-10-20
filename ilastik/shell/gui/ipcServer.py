from SocketServer import BaseRequestHandler, TCPServer, ThreadingMixIn
import socket
import json
from threading import Thread, Event
from Queue import Queue
import logging
from PyQt4 import QtGui
from choosePortDialog import Ui_ChoosePortDialog
import atexit

logger = logging.getLogger(__name__)


class IPCHandler(BaseRequestHandler):
    SOCKET_TIMEOUT = 1
    SOCKET_READ_BYTES = 1024

    def handle(self):
        self.request.settimeout(IPCHandler.SOCKET_TIMEOUT)
        status, name = self._authenticate
        if status:
            #host, port = self.request.getpeername()
            #TODO: Add connection to array?
            self._loop(name)

    def _authenticate(self):
        while not self.server.stop_event.is_set():
            try:
                data = self.request.recv(IPCHandler.SOCKET_READ_BYTES).strip()
            except socket.timeout:  # no problem
                continue
            except socket.error as error:
                logger.exception(error)
                return False, None
            if data == "":
                return False, None
            try:
                message = json.loads(data)
            except ValueError:
                #ignore
                return False, None
            if "command" in message and message["command"] == "handshake"\
                    and "name" in message:
                #TODO: Check if <name> is allowed to connect!
                return True, message["name"]
        return False, None

    def _loop(self, name):
        queue = self.server.queue
        while not self.server.stop_event.is_set():
            try:
                data = self.request.recv(IPCHandler.SOCKET_READ_BYTES).strip()
                if data == "":  # connection closed
                    #TODO: Notify connection close
                    return
                command = json.loads(data)
                queue.put((name, command))
            except socket.timeout:
                # no problem
                continue
            except socket.error as error:
                logger.exception(error)
                return
            except ValueError:
                # ignore
                continue


class IPCServer(ThreadingMixIn, TCPServer):
    pass


class IPCManager(object):
    STOP = object()  # sentinel

    def __init__(self, parent, host=None, port=None):
        self.parent = parent
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.cmd_thread = None
        self.clients = {}

    # setup and start the server
    # promt for port if port is taken
    def start(self):
        if self.server is not None:
            return
        dialog = ChoosePortDialog(self.parent, self.port)
        server = None
        while self.server is None:
            try:
                server = IPCServer((self.host, self.port), IPCHandler)
            except socket.error as socketError:
                dialog.set_error(str(socketError))
                if dialog.exec_() == 0:  # Cancel/Abort
                    logger.warning("IPCServer setup aborted (by user)")
                    return
                self.port = dialog.get_port()
        self.server = server
        self.server.stop_event = Event()
        self.server.queue = Queue()
        self.server_thread = Thread(target=self.server.serve_forever, name="ilastik IPCServer Thread")
        self.server_thread.daemon = True
        self.server_thread.start()
        self.cmd_thread = Thread(target=self._process_cmds, name="ilastik CMD Thread")
        atexit.register(self.stop)
        logger.info("IPCServer setup and running")

    # stop all threads and the server
    # close all client connections
    def stop(self):
        self.server.stop_event.set()
        self.server.shutdown()
        self.server.queue.put(IPCManager.STOP)
        for client in self.clients.itervalues():
            client.close()
        logger.info("IPCServer stopped")

    # send command to all clients
    # commmand is a python dict
    # add filter (optional)
    #   f(host, port, name) => True/False
    def broadcast(self, command, filter_=lambda h, p, n: True):
        data = json.dumps(command)
        for key, client in self.clients.iteritems():
            if filter_(*key):
                client.sendall(data)

    def connect(self, host, port, name):
        if (host, port, name) in self.clients:
            logger.warning("Connection to (%s %s:%d) already established" % (name, host, port))
            return
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
        except socket.error as error:
            logger.exception(error)
            return
        self.clients[(host, port, name)] = client

    def disconnect(self, host, port, name):
        if(host, port, name) in self.clients:
            self.clients[(host, port, name)].close()
            del self.clients[(host, port, name)]

    def _process_cmds(self):
        queue = self.server.queue
        while True:
            item = queue.get()
            if item is IPCManager.STOP:
                return
            # process

    def __del__(self):
        self.stop()


class ChoosePortDialog(QtGui.QDialog):
    def __init__(self, parent, default_port):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_ChoosePortDialog()
        self.ui.setupUi(self)
        self.validator = QtGui.QIntValidator(0, 65535)
        self.ui.port.setValidator(self.validator)
        self.ui.port.setText(default_port)

    def get_port(self):
        try:
            port = int(self.ui.port.text())
        except ValueError:
            return None
        return port

    def set_error(self, error):
        self.ui.error.setText(error)
