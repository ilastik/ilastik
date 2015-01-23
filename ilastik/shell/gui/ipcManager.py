from SocketServer import BaseRequestHandler, TCPServer
from abc import ABCMeta, abstractmethod, abstractproperty
from operator import itemgetter
import socket
import logging
import threading
import atexit
import json
from Queue import Queue
from collections import OrderedDict

from ilastik.widgets.ipcserver.tcpServerInfoWidget import TCPServerInfoWidget
from ilastik.widgets.ipcserver.zmqPublisherInfoWidget import ZMQPublisherInfoWidget

try:
    import zmq
except ImportError:
    zmq = None
from sys import platform as platform_
from PyQt4.QtGui import QInputDialog

from ilastik.widgets.ipcserver.ipcServerInfoWindow import IPCServerInfoWindow
from ilastik.utility.commandProcessor import CommandProcessor
from ilastik.utility.decorators import lazy
from ilastik.utility.singleton import Singleton
from ilastik.utility.ipcProtocol import Protocol
from ilastik.utility.numpyJsonEncoder import NumpyJsonEncoder

logger = logging.getLogger(__name__)


class IPCFacade(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.info = IPCServerInfoWindow()
        self.senders = {}

    def add_sender(self, name, server):
        if name in self.senders:
            raise RuntimeError("Server {} already exists".format(name))
        self.senders[name] = server
        self.info.add_server(name, server.widget)

    @property
    def sending(self):
        return (server.sending for server in self.senders.itervalues())

    def start(self, name=None):
        if name is None:
            for sender in self.senders.itervalues():
                sender.start()
        else:
            self.senders[name].start()

    def stop(self, name=None):
        if name is None:
            for sender in self.senders.itervalues():
                sender.stop()
        else:
            self.senders[name].stop()

    @lazy
    def broadcast(self, command):
        #from pprint import PrettyPrinter
        #PrettyPrinter(indent=4).pprint(command)
        message = json.dumps(command, cls=NumpyJsonEncoder)
        log = Protocol.verbose(command)
        for server in self.senders.itervalues():
            server.broadcast(message, log)

    def show_info(self):
        self.info.show()


class AddressAlreadyTaken(Exception):
    def __init__(self, what):
        self._what = what

    @property
    def what(self):
        return self._what


class Sender(object):
    __metaclass__ = ABCMeta

    def __init__(self, shell):
        self.shell = shell
        self.cmd_processor = CommandProcessor(shell)

    @staticmethod
    def available(mode=None):
        return True

    @abstractproperty
    def running(self):
        """
        :return: True if the server is currently running False otherwise
        """
        pass

    def address_prompt(self, message=""):
        """
        Get a new address from the user ( via dialog )
        :param message: why it is neccessary to ask for a new address
        :type message: str
        :return: tuple ( type: new address, bool: ok_clicked )
        """
        return None

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
            while True:
                try:
                    self._start()
                except AddressAlreadyTaken as e:
                    new_address, ok = self.address_prompt(e.what)
                    if not ok:
                        return
                    self.change_address(new_address)
                else:
                    return

    def stop(self, kill=True):
        """
        Stop the server if it is running
        """
        if self.running:
            self._stop(kill)

    def toggle(self):
        """
        Stop if running, start if not running
        """
        if self.running:
            self._stop()
        else:
            self.start()

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


class TCPHiliteServer(Sender):
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
        super(TCPHiliteServer, self).__init__(shell)
        self.server = None
        self.queue = None
        self.queue_thread = None
        self.port = self.DEFAULT_PORT

        self.info = TCPServerInfoWidget()
        self.info.statusToggled.connect(self.toggle)
        self.info.connectionChanged.connect(self.change_connection)
        self.info.broadcast.connect(self.broadcast)
        self.info.changePort.connect(self.on_address_change)
        self.info.notify_server_status_update("port", self.port)

        self.connections = OrderedDict()

        atexit.register(self.stop, kill=True)

    def on_address_change(self):
        port, ok = self.address_prompt(level="Info")
        if ok:
            self.change_address(port)

    def address_prompt(self, message="", level="Warning"):
        message = "{}. Change port".format(message)
        # noinspection PyTypeChecker
        return QInputDialog.getInt(None, level, message, self.port, 1024, 65535)

    def _start(self):
        try:
            self.server = TCPServer(("0.0.0.0", self.port), Handler)
        except socket.error as e:
            self.server = None
            self.info.notify_server_status_update("running", False)
            if e.errno in [13, 98]:  # Permission denied or Address already in use
                raise AddressAlreadyTaken(str(e))
            raise
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
            s = socket.socket()
            try:
                s.connect(client)
                s.sendall(message)
            except socket.error as e:
                logger.exception("broadcast to %s:%s failed (%s)" % (client[0], client[1], e))
            else:
                count += 1
            finally:
                s.close()

    def _change_address(self, address):
        """
        Changes the server port to the new port
        The server must be shutdown to change the port
        :param address: the new port
        :type address: int
        """
        self.port = address
        self.info.notify_server_status_update("port", address)


class ZMQHilitePublisher(Sender):
    def __init__(self, shell, address):
        super(ZMQHilitePublisher, self).__init__(shell)
        self.address = address

        self.context = zmq.Context()
        self.socket = None
        self.info = ZMQPublisherInfoWidget()
        self.info.statusToggled.connect(self.toggle)
        self.info.notify_server_status_update("address", address)

        atexit.register(self.stop)

    def _change_address(self, address):
        self.address = address
        self.info.notify_server_status_update("port", address)

    @staticmethod
    def available(mode=None):
        if zmq is None:
            return False
        if "tcp" in mode:
            return True
        elif "ipc" in mode:
            return platform_ in ["linux", "linux2"]
        else:
            return False

    def _broadcast(self, message):
        self.socket.send_string(message)

    @property
    def running(self):
        return self.socket is not None

    @property
    def widget(self):
        return self.info

    def _start(self):
        pub = self.context.socket(zmq.PUB)
        try:
            pub.bind(self.address)
        except zmq.ZMQError as e:
            self.info.notify_server_status_update("running", False)
            if e.errno == 98:  # Address already in use
                raise AddressAlreadyTaken
            raise
        self.socket = pub
        self.info.notify_server_status_update("running", True)

    def _stop(self, kill=None):
        self.socket.unbind(self.address)
        self.socket.close()
        self.socket = None
        if kill:
            return
        self.info.notify_server_status_update("running", False)


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

AvailableIPCSenders = [
    ("TCP Server", TCPHiliteServer, None),
    ("ZMQ TCP Publisher", ZMQHilitePublisher, "tcp://*:9998"),
    ("ZMQ IPC Publisher", ZMQHilitePublisher, "ipc:///tmp/ilastik"),
]