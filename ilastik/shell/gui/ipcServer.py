from SocketServer import BaseRequestHandler, TCPServer
import socket
import logging
import threading
import atexit
import json
from Queue import Queue
from collections import OrderedDict

from ilastik.widgets.ipcServerInfoWidget import IPCServerInfoWidget, ChoosePortDialog

logger = logging.getLogger(__name__)


def p(mode):
    def inner(*args):
        print mode, ": ",
        print args
    return inner

logger.info = p("info")
logger.debug = p("debug")
logger.exception = p("exception")


class IPCServerManager(object):
    DEFAULT_PORT = 9999

    """
    manages the IPC Server
    """
    def __init__(self):
        self.server = None
        self.queue = None
        self.queue_thread = None
        self.port = self.DEFAULT_PORT
        self.info = IPCServerInfoWidget()
        self.info.statusToggled.connect(self.toggle_server)
        self.info.connectionChanged.connect(self.change_connection)
        self.connections = OrderedDict()

    """
    Start the server if it is not already running
    Asks for a port if the default port is already used
    """
    def start_server(self, port=None):
        if port is not None:
            self.port = port
        if self.server is not None:
            logger.debug("IPC Server is already running")
            return

        try:
            self.server = TCPServer(("0.0.0.0", self.port), Handler)
            self.queue = Queue()
            self.server.queue = self.queue
        except socket.error as e:
            self.server = None
            if e.errno == 98:  # Address already in use
                dialog = ChoosePortDialog(str(self.port), self.info)
                dialog.set_error(str(e))
                if dialog.exec_():
                    self.start_server(dialog.get_port())
                else:
                    self.info.server_running(False)
                    return
        self.queue_thread = threading.Thread(target=self._handle_queue)
        self.queue_thread.daemon = True
        self.queue_thread.start()

        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        logger.info("IPC Server started on port %d" % self.server.socket.getsockname()[1])
        atexit.register(self.stop_server)
        self.info.server_running(True, self.port)

    """
    Start the server if it is not already shutdown
    """
    def stop_server(self):
        if self.server is not None:
            self.server.shutdown()
            self.info.server_running(False)
            logger.info("IPC Server stopped")
            self.server = None
            self.queue.put(None)
            self.queue_thread = None
            self.connections = {}
            self.info.connections_changed(self.connections)
        else:
            logger.debug("IPC Server is not running")

    """
    starts if not started etc.
    """
    def toggle_server(self):
        if self.server is None:
            self.start_server()
        else:
            self.stop_server()

    """
    Shows a widget that displays information about the server
    """
    def show_info(self):
        self.info.show()

    def add_connection(self, name, host, server_port):
        if (name, host) not in self.connections:
            self.connections[(name, host)] = {"enabled": True}
            self.info.connections_changed(self.connections)

    def change_connection(self, index, enabled):
        self.connections.values()[index]["enabled"] = enabled

    def filter_command(self, cmd):
        self.info.add_command(cmd)
        #todo: redirect to shell


    def _handle_queue(self):
        while True:
            command = self.queue.get()
            if command is None:
                return

            cmd_name = command["command"]
            if cmd_name == "handshake":
                self.add_connection(command["name"], command["host"], command["port"])
            else:
                self.filter_command(command)



class Handler(BaseRequestHandler):
    valid_commands = [
        "handshake",
        "setviewerposition"
    ]
    def handle(self):
        try:
            data = self.request.recv(4096).strip()
        except socket.error as e:
            logger.exception(e)
            return
        try:
            command = json.loads(data)
        except ValueError as e:
            logger.exception(e)
            return
        try:
            command_name = command["command"]
        except KeyError as e:
            logger.exception(e)
            return
        if command_name in self.valid_commands:
            cmd = command
            if command_name == "handshake":
                cmd.update({"host": self.client_address[0]})
            self.server.queue.put(cmd)
        else:
            logger.debug("Unknown command: %s" % command_name)
            return
