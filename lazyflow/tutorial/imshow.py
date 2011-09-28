from PyQt4 import QtCore, QtGui
import qimage2ndarray, vigra, numpy

if QtGui.QApplication.instance() is None:
    qa = QtGui.QApplication([])
else:
    qa = QtGui.QApplication.instance()
    
def imshow(arr):
    if not isinstance(arr,vigra.VigraArray):
        arr = arr.swapaxes(0,1).view(numpy.ndarray)
    im = qimage2ndarray.array2qimage(arr)
    d = QtGui.QDialog()
    l = QtGui.QLabel(d)
    l.setPixmap(QtGui.QPixmap.fromImage(im))
    d.resize(l.sizeHint())
    d.exec_()
