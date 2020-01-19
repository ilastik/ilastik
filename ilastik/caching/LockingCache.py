import threading
from typing import Dict
import time
from collections import deque

def hashable_dict(d):
    return tuple((key, value) for key, value in d.items())

class LockingCache:
    def __init__(self, maxsize=1024):
        self.locks : Dict[threading.Lock] = {}
        self.values = {}
        self.cache_lock = threading.Lock()

        self.maxsize = maxsize
        self.eviction_queue = deque()

    def __call__(self, f):
        def wrapper(*args, **kwargs):
            key = (args, hashable_dict(kwargs))
            with self.cache_lock:
                if key not in self.locks:
                    self.locks[key] = threading.Lock()
            with self.locks[key]:
                if key not in self.values:
                    print("Cache miss -----")
                    self.values[key] = f(*args, **kwargs)
                    self.eviction_queue.append(key)
                    if len(self.eviction_queue) > self.maxsize:
                        print(f"Evicting key {key}")
                        del self.values[self.eviction_queue.popleft()]
                        print(self.eviction_queue)
                else:
                    print("Cache hit +++++")
                return self.values[key]
        return wrapper
