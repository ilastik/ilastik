from SocketServer import BaseRequestHandler, TCPServer
from abc import ABCMeta, abstractmethod, abstractproperty
from functools import partial
from operator import itemgetter
import socket
import logging
import threading
import atexit
import json
from Queue import Queue
from collections import OrderedDict
#import zmq
from PyQt4.QtGui import QInputDialog, QLineEdit
import numpy

from ilastik.widgets.ipcServerInfoWidget import IPCServerInfoWidget
from ilastik.widgets.ipcServerInfoWindow import IPCServerInfoWindow
from ilastik.utility.commandProcessor import CommandProcessor
from ilastik.utility.lazy import lazy

logger = logging.getLogger(__name__)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args)
        return cls._instances[cls]


class Protocol(object):
    ValidOps = ["and", "or"]
    ValidHiliteModes = ["hilite", "unhilite", "toggle", "clear"]

    @staticmethod
    def simple(operator, *wheres, **attributes):
        """
        Builds a simple where clause for the hilite command

        :param wheres: a list of finished where sub clauses
        :param attributes: the attributes and their values to be added
        :returns: the where dict

        e.g.
        simple("and", ilastik_id=42, time=1337)
            => WHERE ( ilastik_id == 42 AND time == 1337 )
        """
        operands = list(wheres)
        for name, value in attributes.iteritems():
            operands.append({
                "operator": "==",
                "row": name,
                "value": value
            })

        return {
            "operator": operator,
            "operands": operands
        }

    @staticmethod
    def simple_in(row, possibilities):
        """
        Builds a simple where clause ( using 'in' ) for the hilite command

        :param row: the row name that must be in possibilities
        :param possibilities: the possible values row can have
        :returns: the where dict

        e.g.
        simple("track_id1", [42, 1337, 12345])
            => WHERE ( track_id1 == 42 OR track_id1 == 1337 OR track_id1 == 12345 )
        """
        operands = []
        for p in possibilities:
            operands.append({
                "operator": "==",
                "row": row,
                "value": p,
            })

        return {
            "operator": "or",
            "operands": operands
        }

    @staticmethod
    def clear():
        """
        Builds the clear hilite command to clear all hilites
        :returns: the command dict
        """
        return {
            "command": "hilite",
            "mode": "clear",
        }

    @staticmethod
    def cmd(mode, where=None):
        if mode.lower() not in Protocol.ValidHiliteModes:
            raise ValueError("Mode '{}' not supported".format(mode))
        command = {
            "command": "hilite",
            "mode": mode
        }
        if where is not None:
            command["where"] = where
        return command

    @staticmethod
    def verbose(command):
        """
        returns the command in an SQL like readable form

        :param command: the command to convert
        :type command: dict
        :returns: the command as str
        """
        assert "command" in command, "Must be a command dict"
        assert command["command"] == "hilite", "Only hilite commands supported"

        mode = command["mode"]
        if mode == "clear":
            return "CLEAR *"
        where = []
        Protocol._parse(where, command["where"])

        return "{} * WHERE {}".format(mode.upper(), " ".join(where))

    @staticmethod
    def _parse(where, sub):
        if "operand" in sub:
            where.append(sub["operator"].upper())
            where.append("(")
            Protocol._parse(where, sub["operand"])
            where.append(")")
        elif "operands" in sub:
            if not sub["operands"]:
                where.append("MISSING")
                where.append(None)
            for operand in sub["operands"]:
                where.append("(")
                Protocol._parse(where, operand)
                where.append(")")
                where.append(sub["operator"].upper())
            where.pop()
        else:
            where.append(sub["row"])
            where.append(sub["operator"].upper())
            where.append(str(sub["value"]))


class IPCServerFacade(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.info = IPCServerInfoWindow()
        self.servers = {}

    def add_server(self, name, server):
        if name in self.servers:
            raise RuntimeError("Server {} already exists".format(name))
        self.servers[name] = server
        self.info.add_server(name, server.widget)

    @property
    def all_running(self):
        return all(server.running for server in self.servers.itervalues())

    @property
    def any_running(self):
        return any(server.running for server in self.servers.itervalues())

    def start(self, name=None):
        if name is None:
            for server in self.servers.itervalues():
                server.start()
        else:
            self.servers[name].start()

    def stop(self, name=None):
        if name is None:
            for server in self.servers.itervalues():
                server.stop()
        else:
            self.servers[name].stop()

    @lazy
    def broadcast(self, command):
        #from pprint import PrettyPrinter
        #PrettyPrinter(indent=4).pprint(command)
        message = json.dumps(command, cls=NumpyJsonEncoder)
        log = Protocol.verbose(command)
        for server in self.servers.itervalues():
            server.broadcast(message, log)

    def show_info(self):
        self.info.show()


class NumpyJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj).__module__ == numpy.__name__:
            try:
                return obj.tolist()
            except (ValueError, AttributeError):
                raise RuntimeError("Could not encode Numpy type: {}".format(type(obj)))
        return super(json.JSONEncoder, self).default(obj)


class Server(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def running(self):
        """
        :return: True if the server is currently running False otherwise
        """
        pass

    @abstractproperty
    def widget(self):
        """
        :return: the widget that displays information about this Server
        """
        pass

    def start(self):
        """
        Start the server if it is not running
        """
        if not self.running:
            self._start()

    def stop(self):
        """
        Stop the server if it is running
        """
        if self.running:
            self._stop()

    def toggle(self):
        """
        Stop if running, start if not running
        """
        if self.running:
            self._stop()
        else:
            self._start()

    def broadcast(self, message, log):
        """
        Broadcasts the message
        :param message: the message to broadcast ( will be json encoded )
        :type message: dict
        """
        if self.running:
            self._broadcast(message)
            self.widget.add_sent_command(log, 0)

    @abstractmethod
    def _broadcast(self, message):
        pass

    def change_address(self, address):
        """
        Changes the address. This can only be done if the server is not running
        :param address: the new address
        :type address: depends on implementation ( see subclass )
        """
        if not self.running:
            self._change_address(address)

    @abstractmethod
    def _change_address(self, address):
        pass

    @abstractmethod
    def _start(self):
        pass

    @abstractmethod
    def _stop(self):
        pass


class TCPHiliteServer(Server):
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
        self.info.statusToggled.connect(self.toggle)
        self.info.connectionChanged.connect(self.change_connection)
        self.info.broadcast.connect(self.broadcast)
        self.info.portChanged.connect(self.change_address)
        self.info.notify_server_status_update("port", self.port)

        self.connections = OrderedDict()
        self.shell = shell
        self.cmd_processor = CommandProcessor(shell)

        atexit.register(self._stop, kill=True)

    def _start(self):
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

    def _stop(self, kill=False):
        """
        Start the server if it is not already shutdown
        """
        if self.server is not None:
            self.server.shutdown()
            if kill:
                return
            self.info.notify_server_status_update("running", False)
            logger.info("IPC Server stopped")
            self.server = None
            self.queue.put(None)
            self.queue_thread = None
            self.connections = OrderedDict()
            self.info.update_connections(self.connections)
        else:
            logger.debug("Can't stop, because IPC Server is not running")

    @property
    def running(self):
        return self.server is not None

    @property
    def widget(self):
        return self.info

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

    def _broadcast(self, message, to_all=False):
        """
        creates a socket for each connection and sends the command as json
        :param message: the command
        :type message: str
        :param to_all: if True the cmd is sent to all ( even the disabled ones ) connections
        :type to_all: bool
        """
        count = 0
        for connection in filter(None if to_all else itemgetter("enabled"), self.connections.itervalues()):
            # noinspection PyTypeChecker
            client = connection["client"]
            s = socket.socket()  # default is fine
            try:
                s.connect(client)
                s.sendall(message)
            except socket.error as e:
                logger.exception("broadcast to %s:%s failed (%s)" % (client[0], client[1], e))
            else:
                count += 1
            finally:
                s.close()

    def _change_address(self, port, start=False):
        """
        Changes the server port to the new port
        The server must be shutdown to change the port
        :param port: the new port
        :type port: int
        :param start: starts the server after changing the port if set to True
        :type start: bool
        """
        if self.server is None:
            self.port = port
            self.info.notify_server_status_update("port", port)
            if start:
                self.start()
        else:
            logger.warn("Can't change the port while running")


class ZMQHilitePublisher(Server):
    Prompt = partial(QInputDialog.getText, "Address already in use", "new address", QLineEdit.Normal)

    def __init__(self, address):

        self.address = address

        # todo: add ZMQ
        #self.context = zmq.Context()
        #self.socket = self.context.socket(zmq.PUB)
        self.context = None
        self.socket = None
        from PyQt4.QtGui import QLabel
        self.info = QLabel("NOT IMPLEMENTED")


        self.is_running = False

        atexit.register(self.shutdown)

    def _change_address(self, address):
        pass

    def _broadcast(self, message):
        print "ZMQ will not send yet"
        return
        self.socket.send_string(message)

    @property
    def running(self):
        return self.is_running

    @property
    def widget(self):
        return self.info

    def _start(self):
        if self.is_running:
            logger.debug("ZMQ Publisher already running")
            return

        # todo: add ZMQ
        """
        while not self.is_running:
            try:
                self.socket.bind(self.address)
            except zmq.ZMQError as e:
                if e.errno != 98:
                    raise
                # Address already in use
                address, ok = self.Prompt(self.address)
                if not ok:
                    return
                self.address = address
            else:
                self.is_running = True
        """
    def _stop(self):
        if not self.is_running:
            logger.debug("ZMQ Publisher is not running")
            return

        self.socket.unbind(self.address)

    def shutdown(self):
        #todo: add zmq
        return
        self.socket.close()
        self.context.destroy()


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
