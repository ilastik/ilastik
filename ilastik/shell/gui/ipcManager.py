from SocketServer import BaseRequestHandler, TCPServer as BaseTCPServer
import logging
import threading
import atexit
import json
from itertools import chain
from collections import OrderedDict
from operator import itemgetter

from ilastik.widgets.ipcserver.tcpServerInfoWidget import TCPServerInfoWidget
from ilastik.widgets.ipcserver.zmqPublisherInfoWidget import ZMQPublisherInfoWidget

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


class IPCFacade(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.info = IPCServerInfoWindow()
        self.senders = {}
        self.receivers = {}

    def add_sender(self, name, sender, protocol=None):
        if name in self.senders:
            raise RuntimeError("Sender {} already exists".format(name))
        self.senders[name] = sender
        if protocol:
            self.senders[protocol] = sender
        self.info.add_server(name, sender.widget)

    def add_receiver(self, name, receiver):
        if name in self.receivers:
            raise RuntimeError("Receiver {} already exists".format(name))
        self.receivers[name] = receiver
        self.info.add_server(name, receiver.widget)

    def sender(self, key):
        return self.senders[key]

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

    @property
    def running(self):
        raise NotImplementedError

    @property
    def widget(self):
        raise NotImplementedError

    @staticmethod
    def available(mode=None):
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
        if command["command"] == "handshake":
            command.update({"protocol": "tcp"})
        command.update({"host": host})

        self.server.queue.put(command)


class TCPServer(Binding):
    def __init__(self, queue):
        self.port = 9999
        self.queue = queue
        self.thread = None
        self.server = None

        self.info = TCPServerInfoWidget()
        self.info.statusToggled.connect(self.toggle)
        self.info.changePort.connect(self.on_address_change)
        self.info.notify_server_status_update("port", self.port)

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
        server.queue = self.queue
        self.server = server

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


class TCPClient(Sending):
    def __init__(self, server):
        self.peers = OrderedDict()
        self.server = server

        self.server.widget.connectionChanged.connect(self.change_peer)

    def add_peer(self, name, host, port):
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
        self.server.widget.update_connections(self.peers)

    def change_peer(self, index, enabled):
        self.peers.values()[index]["enabled"] = enabled

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
        return self.server.widget

    @property
    def running(self):
        return True

    @staticmethod
    def available(mode=None):
        return True


class ZMQHilitePublisher(Binding, Sending):
    def __init__(self, address):
        super(ZMQHilitePublisher, self).__init__()
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
