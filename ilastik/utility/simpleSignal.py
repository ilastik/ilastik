class SimpleSignal(object):
    """
    A simple python-only signal class for implementing the observer pattern.
    For familarity, mimics a SUBSET of the pyqt signal interface.  Not threadsafe.
    No fine-grained unsubcribe mechanism.
    """
    def __init__(self):
        self.subscribers = []

    def connect(self, callable):
        """
        Add a subscriber.
        """
        self.subscribers.append(callable)
    
    def emit(self, *args, **kwargs):
        """
        Fire the signal with the given arguments.
        """
        for f in self.subscribers:
            f(*args, **kwargs)

    def __repr__(self):
        return "SimpleSignal"

    def disconnectAll(self):
        """
        Remove all subscribers.
        """
        self.subscribers = []
            