from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import uic

import os

from volumina.widgets.thresholdingWidget import ThresholdingWidget

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.utility import Tracer

from ilastik.utility import bind

class StopWatch( QWidget ):
    def __init__( self, controls, parent=None ):
        super(StopWatch, self).__init__(parent=parent)

        self.i = None
        self.flag = None
        self._time = None
        self._timer = None
        self._layout = None
        self._hlayout = None
        self._reset = None
        self._start = None
        self._stop = None
        self._num = None
        self._T = 120
        self._ctrls = controls

        self._num = QLCDNumber(self)
	self._num.setNumDigits(8)
	self._time = QTime()
	self._time.setHMS(0,int(self._T/60),0,0)
	self._timer = QTimer(self)
        self._timer.timeout.connect(self.showTime)
	self.i=0
	self._layout = QVBoxLayout(self)
	#self._hlayout = QHBoxLayout(self)
	#self._reset = QPushButton("Reset",self)
        #self._start = QPushButton("Start",self)
	#self._stop = QPushButton("Stop",self)
        self._reset = self._ctrls.reset
        self._start = self._ctrls.start
        self._stop = self._ctrls.stop
        self._ctrls.reset.clicked.connect(self.resetTime)
        self._ctrls.start.clicked.connect(self.startTime)
        self._ctrls.stop.clicked.connect(self.stopTime)

	text = self._time.toString("hh:mm:ss")
	self._num.display(text)
	self._num.setStyleSheet("* { background-color:rgb(199,147,88)color:rgb(255,255,255) padding: 7px}}")
	self._num.setSegmentStyle(QLCDNumber.Filled)
	self.setStyleSheet("* { background-color:rgb(236,219,187)}}")
 
	#self._hlayout.addWidget(self._start)
	#self._hlayout.addWidget(self._stop)
	#self._hlayout.addWidget(self._reset)
	self._layout.addWidget(self._num)
	#self._layout.addLayout(self._hlayout)
	self.setLayout(self._layout)
	self.resize(300,150)

    def resetTime( self ):
	self._time.setHMS(0,int(self._T/60),0)
	text = self._time.toString("hh:mm:ss")
	self._num.display(text)
	self.i=0
	self._stop.setDisabled(1)
	self._start.setEnabled(1)
	self.stopTime()
 
    def startTime( self ):
        self._start.setDisabled(1)
        self._stop.setEnabled(1)
        self._reset.setEnabled(1)
        self._timer.start(1000)
 
    def stopTime( self ):
        self._stop.setDisabled(1)
        self._start.setEnabled(1)
        self._reset.setEnabled(1)
 
        self._timer.stop()

    def showTime( self ):
	self.i=self.i+1
	newtime=self._time.addSecs(-1*self.i)
	text = newtime.toString("hh:mm:ss")
	self._num.display(text)

        if self.i == self._T:
            self.stopTime()
            self.resetTime()

class StopWatchControls( QWidget ):
    def __init__( self, parent=None ):
        super(StopWatchControls, self).__init__(parent=parent)
	self.reset = QPushButton("Reset",self)
        self.start = QPushButton("Start",self)
	self.stop = QPushButton("Stop",self)
	#self.setStyleSheet("* { background-color:rgb(236,219,187)}}")
 
	self._hlayout = QHBoxLayout(self)
	self._hlayout.addWidget(self.start)
	self._hlayout.addWidget(self.stop)
	self._hlayout.addWidget(self.reset)
	self.setLayout(self._hlayout)
    

class StopWatchGui(object):
    """
    """
    
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################

    def centralWidget( self ):
        return self.watch

    def appletDrawer(self):
        return self.watchctrl
        
    def menus( self ):
        return []

    def viewerControlWidget( self ):
        return QLabel("ViewerControl")

    def __init__(self, topLevelOperatorView):
        self.watchctrl = StopWatchControls()
        self.watch = StopWatch( self.watchctrl)

if __name__=='__main__':
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication([])
    ctrl = StopWatchControls()
    watch = StopWatch(ctrl)
    watch.show()
    ctrl.show()
    app.exec_()
