from future import standard_library
standard_library.install_aliases()
from socketserver import BaseRequestHandler, TCPServer as BaseTCPServer
import logging
import threading
import atexit
import json
from itertools import chain
from collections import OrderedDict
from operator import itemgetter
from PyQt5.QtCore import QObject, pyqtSignal
from ilastik.utility.commandProcessor import CommandProcessor
from future.utils import with_metaclass

try:
    import zmq
except ImportError:
    zmq = None
from sys import platform as platform_
from PyQt5.QtWidgets import QInputDialog

from ilastik.widgets.ipcserver.ipcServerInfoWindow import IPCServerInfoWindow
from ilastik.utility.decorators import lazy
from ilastik.utility.singleton import Singleton
from ilastik.utility.ipcProtocol import Protocol
from ilastik.utility.numpyJsonEncoder import NumpyJsonEncoder
from ilastik.utility.contextSocket import socket, socket_error
from ilastik.config import cfg as ilastik_config

logger = logging.getLogger(__name__)


class IPCFacade(with_metaclass(Singleton, object)):
    """
    The Singleton that encapsulates all IPC functionality
    Use this to register new server modules or send broadcasts
    """

    def __init__(self):
        self.info = IPCServerInfoWindow()
        self.senders = {}
        self.receivers = {}
        self.widgets = {}
        self.protocol_map = {}
        self.processor = CommandProcessor()

    def register_shell(self, shell):
        """
        This sets the shell. Must be called before incoming command can be executed
        :param shell: the ilastik shell
        """
        self.processor.set_shell(shell)

    def register_widget(self, widget, title, key):
        """
        Add a new widget to the IPCServerWindow
        :param widget: the widget to add
        :param title: the title to appear in the tab bar
        :param key: the key to identify and reference the widget
        """
        if key in self.widgets:
            raise RuntimeError("Widget {} already exists".format(key))
        self.widgets[key] = widget
        self.info.add_widget(title, widget)

    def register_module(self, module, type_, key, widget_key=None, protocol=None, start=False):
        """
        Adds a new module to the IPCServer
        :param module: the module e.g. TCPServer, ZMQPublisher
        :param type_: "sender" or "receiver"
        :param key: the key to identify the module later
        :param widget_key: a reference to the view widget. If not None the module will connect to it
        :param protocol: set this to redirect handshake command with the matching protocol to this module
        :param start: if set the module will start immediately
        """
        if type_ == "receiver":
            container = self.receivers
            self.processor.connect_receiver(module)
        elif type_ == "sender":
            container = self.senders
        else:
            raise RuntimeError("Type {} is invalid".format(type_))

        if key in container:
            raise RuntimeError("{} {} already exists".format(type_, key))
        container[key] = module
        if widget_key is not None:
            module.connect_widget(self.widgets[widget_key])
        if protocol is not None:
            self.protocol_map[protocol] = module

        if start:
            module.start()

    def handshake(self, protocol, name, address):
        """
        Redirects a handshake command to the registered module
        Currently only TCPClient handles handshake commands from TCPServer
        :param protocol: the protocol to identify the handler ( e.g. tcp )
        :param name: the name of the peer ( e.g. KNIME )
        :param address: the address of the peer. Depends on the protocol ( e.g. for tcp => (str: host, int: port)
        """
        if protocol not in self.protocol_map:
            raise RuntimeError("No such protocol {}".format(protocol))
        self.protocol_map[protocol].add_peer(name, address)

    @property
    def sending(self):
        """
        Check if the senders are running ( e.g. any(IPCFacade().running) or all(IPCFacade().running)
        :return: a list containing True or False for each sender
        """
        return (sender.running for sender in self.senders.values())

    @property
    def receiving(self):
        """
        The same as IPCFacade.sending for the receivers
        """
        return (rec.running for rec in self.receivers.values())

    def start(self):
        """
        Start all registered modules
        """
        for module in self._all_modules():
            module.start()

    def stop(self):
        """
        Stop all registered modules
        """
        for module in self._all_modules():
            module.stop()

    def _all_modules(self):
        return chain(iter(self.senders.values()), iter(self.receivers.values()))

    @lazy
    def broadcast(self, command):
        """
        Creates functions that can directly be passed to Qt's connect mechanism
        e.g.
            action = IPCFacade().broadcast( ... a command ... )
            qtSignal.connect(action)
        :param command: the command ( dict )
        """
        #from pprint import PrettyPrinter
        #PrettyPrinter(indent=4).pprint(command)
        message = json.dumps(command, cls=NumpyJsonEncoder)
        log = Protocol.verbose(command)
        for server in self.senders.values():
            server.broadcast(message, log)

    def show_info(self):
        """
        Displays the IPC Info Widget or moves the windows to the top
        :return:
        """
        self.info.show()
        self.info.activateWindow()  # bring to top


class InvalidAddress(Exception):
    """
    raise this inside IPCModule._start to automaticely prompt for a new address
    """
    def __init__(self, what):
        self._what = what

    @property
    def what(self):
        return self._what


class IPCModul(object):
    """
    The base class for the IPC modules registered in the IPCFacade
    """
    def start(self):
        pass

    @property
    def running(self):
        """
        Implement this to return if the module is currently running or not
        """
        raise NotImplementedError

    @property
    def widget(self):
        """
        :return: the info widget of the IPC module
        """
        raise NotImplementedError

    def connect_widget(self, widget):
        """
        This will be called by the IPCFacade to connect the module to its widget
        :param widget: the QtWidget
        """
        raise NotImplementedError

    @staticmethod
    def available(mode=None):
        """
        Implement this to return if the module is available on the current platform
        e.g. ZeroMQ's ipc protocol is only available on UNIX
        :param mode: this can be used to distinguish different modes ( e.g. protocols )
        """
        raise NotImplementedError


class HasPeers(IPCModul):
    """
    Interface for all modules that maintain a list of peers in any way
    """
    def add_peer(self, name, address):
        """
        Call this to add a peer to the list
        :param name: its name ( e.g. KNIME )
        :param address: its address ( depends on the protocol )
        """
        raise NotImplementedError

    def update_peer(self, key, **kvargs):
        """
        Call this to change settings for a peer
        :param key: the internal identifier for the peer ( e.g. the index to the peer list )
        :param kvargs: key-value pairs that should be changed
        """
        raise NotImplementedError


class Sending(IPCModul):
    """
    Interface for all modules that can broadcast messages
    """
    def broadcast(self, message, log):
        """
        Wrapper to only broadcast if running and logging of the message
        """
        if self.running:
            self._broadcast(message)
            self.widget.add_sent_command(log, 0)

    def _broadcast(self, message):
        """
        Implement this to broadcast the message
        :param message: the message to broadcast as a str
        """
        raise NotImplementedError


class Receiving(IPCModul):
    """
    Interface for all modules that can receive messages
    """
    @property
    def signal(self):
        """
        :return: the signal that will be emitted if a message was received
        Signature: ( str: command_name, dict: command_data )
        """
        raise NotImplementedError


class Binding(IPCModul):
    """
    Interface for all modules that must be started as they bind to an address ( that might not be available ) in any way
    """
    def start(self):
        """
        Start the server if it is not running
        This also automatically displays the address_prompt if problem occurred
        """
        if not self.running:
            while True:
                try:
                    self._start()
                except InvalidAddress as e:
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

    def change_address(self, address):
        """
        Changes the address. This can only be done if the server is not running
        :param address: the new address
        :type address: depends on implementation ( see subclass )
        """
        if not self.running:
            self._change_address(address)

    def _start(self):
        """
        Implement this to start the module.
        raise InvalidAddress if the module could not be started
        """
        raise NotImplementedError

    def _stop(self, kill=False):
        """
        Implement this to stop the module
        the module should be able to restart after this
        """
        raise NotImplementedError

    def _change_address(self, address):
        """
        Implement this to change the address of the module
        This will only be called if the module is not running
        """
        raise NotImplementedError

    def address_prompt(self, message):
        """
        Display a graphical window to ask the user for a different address.
        This might happen if the previous address is invalid or simply if the user wanted to change the address
        """
        raise NotImplementedError


class Handler(BaseRequestHandler):
    """
    Basic Handler for the SocketServer
    """
    def handle(self):
        """
        Receive one Message and emit the signal
        """
        try:
            data = self.request.recv(4096).strip()
            host, port = self.request.getpeername()
            if data == "":
                return
            command = json.loads(data)
        except (socket_error, ValueError) as e:
            logger.exception(e)
            return
        name = command.pop("command")
        if name == "handshake":
            command.update({"protocol": "tcp"})
        command.update({"host": host})

        self.server.signal.emit(name, command)


class TCPServer(Binding, Receiving, QObject):
    """
    raw tcp server. accepts handshakes which will be forwarded to the TCPClient
    """
    commandReceived = pyqtSignal(str, dict)

    def __init__(self, interface, port):
        super(TCPServer, self).__init__()
        self.port = port
        self.interface = interface
        self.thread = None
        self.server = None

        self.info = None

    @property
    def signal(self):
        return self.commandReceived

    def connect_widget(self, widget):
        self.info = widget
        widget.statusToggled.connect(self.toggle)
        widget.changePort.connect(self.on_address_change)
        widget.notify_server_status_update("port", self.port)

    def on_address_change(self):
        port, ok = self.address_prompt(level="Info")
        if ok:
            self.change_address(port)

    @staticmethod
    def available(mode=None):
        return True

    @property
    def widget(self):
        return self.info

    @property
    def running(self):
        return self.server is not None

    def _start(self):
        try:
            server = BaseTCPServer((self.interface, self.port), Handler)
        except socket.error as e:
            self.server = None
            self.info.notify_server_status_update("running", False)
            if e.errno in [13, 98]:  # Permission denied or Address already in use
                raise InvalidAddress(str(e))
            raise
        self.server = server
        server.signal = self.signal

        thread = threading.Thread(target=self.server.serve_forever, name="TCPServer Thread")
        thread.daemon = True
        thread.start()
        logger.info("IPC Server started on port %d" % self.server.socket.getsockname()[1])
        self.info.notify_server_status_update("running", True)

        self.thread = thread

    def _stop(self, kill=False):
        self.server.shutdown()
        if kill:
            return
        self.info.notify_server_status_update("running", False)
        logger.info("IPC Server stopped")
        self.server = None

    def address_prompt(self, message="", level="Warning"):
        message = "{}. Change port".format(message)
        return QInputDialog.getInt(QInputDialog(), level, message, self.port, 1024, 65535)

    def _change_address(self, address):
        self.port = address


class TCPClient(Sending, HasPeers):
    """
    This module keeps a list of peers an connects to them if a message must be broadcast
    The tcp connection will be closed right after the messages were sent
    """
    def __init__(self):
        self.peers = OrderedDict()

        self.info = None

    def connect_widget(self, widget):
        self.info = widget
        widget.connectionChanged.connect(self.update_peer)

    def add_peer(self, name, address):
        host, port = address
        key = (host, name)
        if key not in self.peers:
            self.peers[key] = {
                "enabled": ilastik_config.getboolean("ipc raw tcp", "autoaccept"),
                "address": [host, port]
            }

        elif self.peers[key]["address"][1] != port:
            self.peers[key]["address"][1] = port
        else:
            return
        self.info.update_connections(self.peers)

    def update_peer(self, key, **kvargs):
        enabled = kvargs["enabled"]
        list(self.peers.values())[key]["enabled"] = enabled

    def _broadcast(self, message):
        count = 0
        for peer in filter(itemgetter("enabled"), iter(self.peers.values())):
            try:
                with socket() as s:
                    # noinspection PyTypeChecker
                    host, port = peer["address"]
                    s.connect((host, port))
                    s.sendall(message)
            except socket_error as e:
                logger.exception(e)
            else:
                count += 1
        return count

    @property
    def widget(self):
        return self.info

    @property
    def running(self):
        return bool(self.peers)

    @staticmethod
    def available(mode=None):
        return True


class ZMQBase(Binding):
    """
    Base class for the zmq modules
    """
    def __init__(self, protocol, address):
        self.protocol = protocol
        self.address = address

    def address_prompt(self, message="", level="Warning"):
        message = "{}. Change address".format(message)
        return QInputDialog.getText(QInputDialog(), level, message, 0, self.address)

    def on_address_change(self):
        address, ok = self.address_prompt(level="Info")
        if ok:
            self.change_address(address)

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

    @property
    def full_addr(self):
        return "{}://{}".format(self.protocol, self.address)


class ZMQPublisher(ZMQBase, Sending):
    """
    This module publishes the hilite commands
    """
    def __init__(self, protocol, address):
        super(ZMQPublisher, self).__init__(protocol, address)

        self.context = zmq.Context()
        self.socket = None
        self.info = None

        #atexit.register(self.stop)

    def connect_widget(self, widget):
        self.info = widget
        widget.pubStatusToggled.connect(self.toggle)
        widget.notify_server_status_update("pub", "address", self.full_addr)
        widget.changePubAddress.connect(self.on_address_change)

    def _change_address(self, address):
        self.address = address
        self.info.notify_server_status_update("pub", "address", self.full_addr)

    def _broadcast(self, message):
        self.socket.send_string(message, zmq.NOBLOCK)

    @property
    def running(self):
        return self.socket is not None

    @property
    def widget(self):
        return self.info

    def _start(self):
        pub = self.context.socket(zmq.PUB)
        try:
            pub.bind(self.full_addr)
        except zmq.ZMQError as e:
            self.info.notify_server_status_update("pub", "running", False)
            if e.errno in [98, 13]:  # Address already in use
                raise InvalidAddress(str(e))
            raise
        self.socket = pub
        logger.info("ZMQ Publisher started on {}".format(self.full_addr))
        self.info.notify_server_status_update("pub", "running", True)

    def _stop(self, kill=None):
        self.socket.unbind(self.full_addr)
        self.socket.close()
        self.socket = None
        if kill:
            return
        logger.info("ZMQ Publisher {} stopped".format(self.full_addr))
        self.info.notify_server_status_update("pub", "running", False)


class ZMQSubscriber(QObject, ZMQBase, Receiving):
    """
    This module subscribes to all publishers on a given address
    """
    commandReceived = pyqtSignal(str, dict)

    def __init__(self, protocol, address):
        super().__init__(protocol=protocol, address=address)
        self.context = zmq.Context()
        self.socket = None
        self.thread = None
        self.stop_event = threading.Event()

        self.info = None

    @property
    def widget(self):
        return self.info

    def connect_widget(self, widget):
        self.info = widget
        widget.subStatusToggled.connect(self.toggle)
        widget.changeSubAddress.connect(self.on_address_change)
        widget.notify_server_status_update("sub", "address", self.full_addr)
        self.signal.connect(widget.add_recv_command)

    def _change_address(self, address):
        self.address = address
        self.info.notify_server_status_update("sub", "address", self.full_addr)

    @property
    def running(self):
        return self.socket is not None

    @property
    def signal(self):
        return self.commandReceived

    def _start(self):
        # noinspection PyArgumentList
        s = self.context.socket(zmq.SUB)
        s.setsockopt(zmq.SUBSCRIBE, "")
        s.connect(self.full_addr)
        self.socket = s

        self.stop_event.clear()
        thread = threading.Thread(target=self.serve, name="ZMQ Sub {} Thread".format(self.protocol))
        thread.daemon = True
        thread.start()
        self.thread = thread
        logger.info("ZMQ Subscriber started on {}".format(self.full_addr))
        self.info.notify_server_status_update("sub", "running", True)

    def _stop(self, kill=False):
        self.stop_event.set()
        self.thread.join()
        self.socket.disconnect(self.full_addr)
        self.socket.close()
        self.socket = None
        logger.info("ZMQ Subscriber {} stopped".format(self.full_addr))
        self.info.notify_server_status_update("sub", "running", False)

    def serve(self):
        poll = zmq.Poller()
        poll.register(self.socket, zmq.POLLIN)
        while not self.stop_event.is_set():
            s = dict(poll.poll(1000))
            if s.get(self.socket) == zmq.POLLIN:
                command = self.socket.recv_json()
                name = command.pop("command")
                self.signal.emit(name, command)
