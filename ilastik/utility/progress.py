from __future__ import print_function, absolute_import, nested_scopes, generators, division, with_statement, unicode_literals
import sys

class ProgressBar:
    def __init__(self, start=0, stop=100):
        self._state = 0
        self._start = start
        self._stop = stop

    def reset(self, val=0):
        self._state = val

    def show(self, increase=1):
        self._state += increase
        if self._state > self._stop:
            self._state = self._stop

        # show
        pos = float(self._state - self._start)/(self._stop - self._start)
        try:
            sys.stdout.write("\r[%-20s] %d%%" % ('='*int(20*pos), (100*pos)))

            if self._state == self._stop:
                sys.stdout.write('\n')
                sys.stdout.flush()
        except IOError:
            pass

class DefaultProgressVisitor:
    def __init__(self):
        pass

    def setState(self,name):
        pass

    def showState(self,name):
        pass

    def showProgress(self, pos):
        pass

class CommandLineProgressVisitor(DefaultProgressVisitor):
    def __init__(self, start=0, stop=1.0):
        self.state = "State"
        self._state = start
        self._start = start
        self._stop = stop

    def setState(self,name):
        self.state=name

    def showState(self,name="State"):
        if not name=="State":
            self.state=name
        try:
            sys.stdout.write(self.state+'\n')
        except IOError:
            pass

    def showProgress(self,pos):
        self._state = pos
        if self._state > self._stop:
            self._state = self._stop

        pos = float(pos)
        try:
            sys.stdout.write("\r[%-20s] %d%%" % ('='*int(20*pos), (100*pos)))

            if self._state >= self._stop:
                sys.stdout.write('\n')
                sys.stdout.flush()
        except IOError:
            pass

