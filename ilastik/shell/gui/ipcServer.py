from SocketServer import BaseRequestHandler, TCPServer
from operator import itemgetter
import socket
import logging
import threading
import atexit
import json
from Queue import Queue
from collections import OrderedDict

from ilastik.widgets.ipcServerInfoWidget import IPCServerInfoWidget
from ilastik.utility.commandProcessor import CommandProcessor

logger = logging.getLogger(__name__)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args)
        return cls._instances[cls]


class IPCServerFacade(object):
    """
    Singleton for access to the ServerManager
    """
    __metaclass__ = Singleton

    def __init__(self):
        self.server = None

    def convert_id_by_config(self, id_, time=0):
        """
        Converts the id used in ilastik to the id used in the Exporter
        :param id_: the id in ilastik
        :param time: the frame number
        :return: the id used in the exporter
        """
        #todo: read config first
        return id_ - 1

    def set_server(self, server):
        """
        Sets the server that will receive all messages
        :param server: the server to set
        :type server: IPCServerManager
        """
        self.server = server

    def is_running(self):
        """
        :returns: True if the server is running else False
        """
        if self.server is None:
            return False
        return self.server.is_running()

    def hilite(self, object_id, time=0):
        """
        Sends a hilite command to all clients
        :param object_id: the id of the object that should be hilited
        """
        if self.server is None:
            logger.debug("no server")
            return False
        object_id = self.convert_id_by_config(object_id)
        self.server.broadcast(command=0, objectid="Row%d" % object_id)
        logger.debug("hiliting object '%d'" % object_id)

    def unhilite(self, object_id, time=0):
        """
        Sends an unhilite command to all clients
        :param object_id: the id of the object that should be unhilited
        """
        if self.server is None:
            logger.debug("no server")
            return False
        object_id = self.convert_id_by_config(object_id)
        self.server.broadcast(command=1, objectid="Row%d" % object_id)
        logger.debug("unhiliting object '%d'" % object_id)

    def clear_hilite(self):
        """
        Sends a clearhilite command to all clients
        So all object will be unhilited
        """
        if self.server is None:
            logger.debug("no server")
            return False
        self.server.broadcast(command=2)
        logger.debug("clearing hilite")


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
        self.info.portChanged.connect(self.change_port)
        self.info.notify_server_status_update("port", self.port)

        self.connections = OrderedDict()
        self.shell = shell
        self.cmd_processor = CommandProcessor(shell)

        atexit.register(self.stop_server, silent=True)

    def start_server(self):
        """
        Start the server if it is not already running
        Asks for a port if the default port is already used or permissions are too low
        """
        if self.server is not None:
            logger.debug("IPC Server is already running")
            return

        try:
            self.server = TCPServer(("0.0.0.0", self.port), Handler)
        except socket.error as e:
            self.server = None
            if e.errno in [13, 98]:  # Permission denied or Address already in use
                self.info.change_port(self.port, str(e))
            self.info.notify_server_status_update("running", False)
            return
        self.queue = Queue()
        self.server.queue = self.queue
        self.queue_thread = threading.Thread(target=self._handle_queue)
        self.queue_thread.daemon = True
        self.queue_thread.start()

        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        logger.info("IPC Server started on port %d" % self.server.socket.getsockname()[1])
        self.info.notify_server_status_update("running", True)

    def stop_server(self, silent=False):
        """
        Start the server if it is not already shutdown
        """
        if self.server is not None:
            self.server.shutdown()
            self.info.notify_server_status_update("running", False)
            logger.info("IPC Server stopped")
            self.server = None
            self.queue.put(None)
            self.queue_thread = None
            self.connections = OrderedDict()
            self.info.update_connections(self.connections)
        elif not silent:
            logger.debug("Can't stop, because IPC Server is not running")

    def is_running(self):
        """
        :return: True if the server is currently running False otherwise
        """
        return self.server is not None

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
        elif self.connections[(name, host)]["client"][1] != remote_server_port:
            client = self.connections[(name, host)]["client"]
            self.connections[(name, host)]["client"] = (client[0], remote_server_port)

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
        except Exception as e:
            print "Exception", e
        except:
            print "Unknown Error"
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

    def broadcast(self, to_all=False, **kvargs):
        """
        creates a socket for each connection and sends the command as json
        :param command_name: the name of the command
        :type command_name: str
        :param to_all: if True the cmd is sent to all ( even the disabled ones ) connections
        :type to_all: bool
        :param kvargs: the arguments specific for the command
        :type kvargs: any JSON type (int, float, str, bool, list, dict)
        """
        for connection in filter(None if to_all else itemgetter("enabled"), self.connections.itervalues()):
            # noinspection PyTypeChecker
            client = connection["client"]
            command = json.dumps(kvargs)
            s = socket.socket()  # default is fine
            try:
                s.connect(client)
                s.sendall(command)
            except socket.error as e:
                logger.exception("broadcast to %s:%s failed (%s)" % (client[0], client[1], e))
            finally:
                s.close()

    def _broadcast(self, kvargs):
        """
        convenience method for info.broadcast signal
        """
        self.broadcast(**kvargs)

    def change_port(self, port, start_server=False):
        """
        Changes the server port to the new port
        The server must be shutdown to change the port
        :param port: the new port
        :type port: int
        :param start_server: starts the server after changing the port if set to True
        :type start_server: bool
        """
        if self.server is None:
            self.port = port
            self.info.notify_server_status_update("port", port)
            if start_server:
                self.start_server()
        else:
            logger.warn("Can't change the port while running")


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
