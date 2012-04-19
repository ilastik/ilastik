class SimpleSignal(object):
    """
    A simply python-only signal class for implementing the observer pattern.
    Not threadsafe.
    No unsubcribe mechanism.
    """
    def __init__(self):
        self.subscribers = []

    def connect(self, callable):
        self.subscribers.append(callable)
    
    def emit(self, *args, **kwargs):
        for f in self.subscribers:
            f(*args, **kwargs)

