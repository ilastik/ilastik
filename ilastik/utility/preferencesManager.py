import os
import threading
import cPickle as pickle
from ilastik.utility import Singleton

class PreferencesManager():
    __metaclass__ = Singleton

    def get(self, group, setting):
        try:
            return self._prefs[group][setting]
        except KeyError:
            return None

    def set(self, group, setting, value):
        if group not in self._prefs:
            self._prefs[group] = {}
        self._prefs[group][setting] = value
        if not self._poolingSave:
            self._save()

    def __init__(self):
        self._filePath = os.path.expanduser('~/.ilastik_preferences')
        self._lock = threading.Lock()
        self._prefs = self._load()
        self._poolingSave = False

    def _load(self):
        with self._lock:
            if not os.path.exists(self._filePath):
                return {}
            else:
                with open(self._filePath, 'r') as f:
                    return pickle.load(f)
        
    def _save(self):
        with self._lock:
            with open(self._filePath, 'w') as f:
                pickle.dump(self._prefs, f)

    # We support the 'with' keyword, in which case a sequence of settings can be set,
    # and the preferences file won't be updated until the __exit__ function is called.
    # (Otherwise, each call to set() triggers a new save.)
        
    def __enter__(self):
        self._poolingSave = True
        return self
        
    def __exit__(self, *args):
        self._poolingSave = False
        self._save()

if __name__ == "__main__":
    prefsMgr = PreferencesManager()
    prefsMgr2 = PreferencesManager()
    assert id(prefsMgr) == id(prefsMgr2), "It's supposed to be a singleton!"
    
    with PreferencesManager() as prefsMgr:
        prefsMgr.set("Group 1", "Setting1", [1,2,3])
        prefsMgr.set("Group 1", "Setting2", ['a', 'b', 'c'])
        
        prefsMgr.set("Group 2", "Setting1", "Forty-two")
    
    # Force a new instance
    PreferencesManager.instance = None
    prefsMgr = PreferencesManager()
    assert prefsMgr != prefsMgr2, "For this test, I want a separate instance"
    
    assert prefsMgr.get("Group 1", "Setting1") == [1,2,3]
    assert prefsMgr.get("Group 1", "Setting2") == ['a', 'b', 'c']
    
    assert prefsMgr.get("Group 2", "Setting1") == "Forty-two"

