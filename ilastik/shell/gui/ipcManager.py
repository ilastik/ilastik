from SocketServer import BaseRequestHandler, TCPServer as BaseTCPServer
import logging
import threading
import atexit
import json
from itertools import chain
from collections import OrderedDict
from operator import itemgetter
from PyQt4.QtCore import QObject, pyqtSignal
from ilastik.utility.commandProcessor import CommandProcessor

try:
    import zmq
except ImportError:
    zmq = None
from sys import platform as platform_
from PyQt4.QtGui import QInputDialog

from ilastik.widgets.ipcserver.ipcServerInfoWindow import IPCServerInfoWindow
from ilastik.utility.decorators import lazy
from ilastik.utility.singleton import Singleton
from ilastik.utility.ipcProtocol import Protocol
from ilastik.utility.numpyJsonEncoder import NumpyJsonEncoder
from ilastik.utility.contextSocket import socket, socket_error

logger = logging.getLogger(__name__)
def p(*x):
    print x
logger.info = p


class IPCFacade(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.info = IPCServerInfoWindow()
        self.senders = {}
        self.receivers = {}
        self.widgets = {}
        self.protocol_map = {}
        self.processor = CommandProcessor()

    def register_shell(self, shell):
        self.processor.set_shell(shell)

    def register_widget(self, widget, title, key):
        if key in self.widgets:
            raise RuntimeError("Widget {} already exists".format(key))
        self.widgets[key] = widget
        self.info.add_widget(title, widget)

    def register_module(self, module, type_, key, widget_key=None, protocol=None):
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

    def handshake(self, protocol, name, address):
        if protocol not in self.protocol_map:
            raise RuntimeError("No such protocol {}".format(protocol))
        self.protocol_map[protocol].add_peer(name, address)

    @property
    def sending(self):
        return (sender.running for sender in self.senders.itervalues())

    @property
    def receiving(self):
        return (rec.running for rec in self.receivers.itervalues())

    def start(self):
        for module in self._all_modules():
            module.start()

    def stop(self):
        for module in self._all_modules():
            module.stop()

    def _all_modules(self):
        return chain(self.senders.itervalues(), self.receivers.itervalues())

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
        self.info.activateWindow()  # bring to top


class AddressAlreadyTaken(Exception):
    def __init__(self, what):
        self._what = what

    @property
    def what(self):
        return self._what


class IPCModul(object):
    def start(self):
        pass

    @property
    def running(self):
        raise NotImplementedError

    @property
    def widget(self):
        raise NotImplementedError

    def connect_widget(self, widget):
        raise NotImplementedError

    @staticmethod
    def available(mode=None):
        raise NotImplementedError


class HasPeers(IPCModul):
    def add_peer(self, name, address):
        raise NotImplementedError

    def update_peer(self, key, **kvargs):
        raise NotImplementedError


class Sending(IPCModul):
    def broadcast(self, message, log):
        """
        Broadcasts the message
        :param message: the message to broadcast ( will be json encoded )
        :type message: dict
        """
        if self.running:
            self._broadcast(message)
            self.widget.add_sent_command(log, 0)

    def _broadcast(self, message):
        raise NotImplementedError


class Receiving(IPCModul):
    @property
    def signal(self):
        raise NotImplementedError


class Binding(IPCModul):
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

    def change_address(self, address):
        """
        Changes the address. This can only be done if the server is not running
        :param address: the new address
        :type address: depends on implementation ( see subclass )
        """
        if not self.running:
            self._change_address(address)

    def _start(self):
        raise NotImplementedError

    def _stop(self, kill=False):
        raise NotImplementedError

    def _change_address(self, address):
        raise NotImplementedError

    def address_prompt(self, message):
        raise NotImplementedError


class Handler(BaseRequestHandler):
    """
    Basic Handler for the SocketServer
    """
    def handle(self):
        """
        Receive one Message and enqueue it if valid
        Then close the connection as knime does it
        """
        try:
            data = self.request.recv(4096).strip()
            host, port = self.request.getpeername()
            if data == "":
                return
            command = json.loads(data)
        except (socket.error, ValueError) as e:
            logger.exception(e)
            return
        name = command.pop("command")
        if name == "handshake":
            command.update({"protocol": "tcp"})
        command.update({"host": host})

        self.server.signal.emit(name, command)


class TCPServer(Binding, Receiving, QObject):
    commandReceived = pyqtSignal(str, dict)

    def __init__(self):
        super(TCPServer, self).__init__()
        self.port = 9999
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
            server = BaseTCPServer(("0.0.0.0", self.port), Handler)
        except socket.error as e:
            self.server = None
            self.info.notify_server_status_update("running", False)
            if e.errno in [13, 98]:  # Permission denied or Address already in use
                raise AddressAlreadyTaken(str(e))
            raise
        self.server = server
        server.signal = self.signal

        thread = threading.Thread(target=self.server.serve_forever)
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
                "enabled": True,
                "address": [host, port]
            }

        elif self.peers[key]["address"][1] != port:
            self.peers[key]["address"][1] = port
        else:
            return
        self.info.update_connections(self.peers)

    def update_peer(self, key, **kvargs):
        enabled = kvargs["enabled"]
        self.peers.values()[key]["enabled"] = enabled

    def _broadcast(self, message):
        count = 0
        for peer in filter(itemgetter("enabled"), self.peers.itervalues()):
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


class ZMQHilitePublisher(Binding, Sending):
    def __init__(self, address):
        super(ZMQHilitePublisher, self).__init__()
        self.address = address

        self.context = zmq.Context()
        self.socket = None
        self.info = None

        atexit.register(self.stop)

    def connect_widget(self, widget):
        self.info = widget
        widget.statusToggled.connect(self.toggle)
        widget.notify_server_status_update("address", self.address)

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
        logger.info("ZMQ Publisher started on {}".format(self.address))
        self.info.notify_server_status_update("running", True)

    def _stop(self, kill=None):
        self.socket.unbind(self.address)
        self.socket.close()
        self.socket = None
        if kill:
            return
        self.info.notify_server_status_update("running", False)
