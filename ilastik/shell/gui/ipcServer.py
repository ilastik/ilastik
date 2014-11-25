from SocketServer import BaseRequestHandler, TCPServer
import socket
import logging
import threading
import atexit
import json
from Queue import Queue
from collections import OrderedDict

from ilastik.widgets.ipcServerInfoWidget import IPCServerInfoWidget, ChoosePortDialog
from ilastik.utility.commandProcessor import CommandProcessor

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
    """
    This ServerManager updates the IPCServerInfoWidget,
    starts/stops the server, adds connections and forwards
    commands to the command processor
    """
    DEFAULT_PORT = 9999

    def __init__(self, shell):
        """
        :param shell: the shell for the CommandProcessor
        :type shell: IlastikShell
        """
        self.server = None
        self.queue = None
        self.queue_thread = None
        self.port = self.DEFAULT_PORT
        self.info = IPCServerInfoWidget()
        self.info.statusToggled.connect(self.toggle_server)
        self.info.connectionChanged.connect(self.change_connection)
        self.info.broadcast.connect(self._broadcast)
        self.connections = OrderedDict()
        self.shell = shell
        self.cmd_processor = CommandProcessor(shell)

    def start_server(self, port=None):
        """
        Start the server if it is not already running
        Asks for a port if the default port is already used
        :param port: the port the socket will be listening on, None for default
        :type port: int or None
        """
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
                    self.info.set_server_running(False)
                    return
        self.queue_thread = threading.Thread(target=self._handle_queue)
        self.queue_thread.daemon = True
        self.queue_thread.start()

        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        logger.info("IPC Server started on port %d" % self.server.socket.getsockname()[1])
        atexit.register(self.stop_server)
        self.info.set_server_running(True, self.port)

    def stop_server(self):
        """
        Start the server if it is not already shutdown
        """
        if self.server is not None:
            self.server.shutdown()
            self.info.set_server_running(False)
            logger.info("IPC Server stopped")
            self.server = None
            self.queue.put(None)
            self.queue_thread = None
            self.connections = {}
            self.info.update_connections(self.connections)
        else:
            logger.debug("IPC Server is not running")

    def toggle_server(self):
        """
        starts if not started etc.
        """
        if self.server is None:
            self.start_server()
        else:
            self.stop_server()

    def show_info(self):
        """
        Shows a widget that displays information about the server
        """
        self.info.show()

    def add_connection(self, name, host, remote_server_port):
        """
        Adds an entry for the new client and notifies the InfoWidget
        :param name: name of the remote program [knime]
        :type name: str
        :param host: the ip address of the remote program
        :type host: str
        :param remote_server_port: the port of the remote program
        :type remote_server_port: int
        """
        if (name, host) not in self.connections:
            self.connections[(name, host)] = {
                "enabled": True,
                "client": (host, remote_server_port)
            }
            self.info.update_connections(self.connections)

    def change_connection(self, index, enabled):
        """
        This is connected to the connectionChanged signal from the InfoWidget
        :param index: the index of the connection in the OrderedDict
        :type index: int
        :param enabled: the status the connection will change to
        :type enabled: bool
        """
        self.connections.values()[index]["enabled"] = enabled

    def filter_command(self, cmd):
        """
        Executes the command if the remote client is allowed to
        :param cmd: the command to filter
        :type cmd: dict
        """
        #todo: filter
        del cmd["host"]
        success = True
        # noinspection PyBroadException
        try:
            self.cmd_processor.execute(cmd["command"], cmd)
        except Exception:
            success = False
        self.info.add_command(cmd, success)

    def _handle_queue(self):
        """
        handles each command in the queue until closed
        """
        while True:
            command = self.queue.get()
            if command is None:
                return

            cmd_name = command["command"]
            if cmd_name == "handshake":
                self.add_connection(command["name"], command["host"], command["port"])
            else:
                self.filter_command(command)

    def broadcast(self, command_name, **kvargs):
        """
        creates a socket for each connection and sends the command as json
        :param command_name: the name of the command
        :type command_name: str
        :param kvargs: the arguments specific for the command
        :type kvargs: any JSON type (int, float, str, bool, list, dict)
        """
        for connection in self.connections.itervalues():
            client = connection["client"]
            kvargs.update({
                "command": command_name
            })
            command = json.dumps(kvargs)
            s = socket.socket()  # default is fine
            try:
                s.connect(client)
                s.sendall(command)
            except socket.error as e:
                logger.exception("broadcast to %s:%s failed (%s)" % (client[0], client[1], e))
            finally:
                s.close()

    def _broadcast(self, command_name, kvargs):
        """
        convenience method for info.broadcast signal
        """
        self.broadcast(str(command_name), **kvargs)


class Handler(BaseRequestHandler):
    """
    Basic Handler for the SocketServer
    """
    valid_commands = [
        "handshake",
        "setviewerposition"
    ]

    def handle(self):
        """
        Receive one Message and enqueue it if valid
        Then close the connection as knime does it
        """
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
            cmd.update({"host": self.client_address[0]})
            self.server.queue.put(cmd)
        else:
            logger.debug("Unknown command: %s" % command_name)
            return
