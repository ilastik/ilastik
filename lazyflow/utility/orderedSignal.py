
class OrderedSignal(object):
    """
    A callback mechanism that ensures callbacks occur in the same order as subscription.
    """
    def __init__(self):
        self.callbacks = []

    def subscribe(self, fn, **kwargs):
        # Remove this function if we already have it
        self.unsubscribe(fn)
        # Add it to the end
        self.callbacks.append((fn, kwargs))

    def unsubscribe(self, fn):
        # Find this function and remove its entry
        for i, (f, kw) in enumerate(self.callbacks):
            if f == fn:
                self.callbacks.pop(i)
                break

    def __call__(self, *args):
        """
        Emit the signal.
        """
        for f, kw in self.callbacks:
            f(*args, **kw)
