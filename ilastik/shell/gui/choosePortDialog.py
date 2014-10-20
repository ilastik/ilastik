# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'choosePortDialog.ui'
#
# Created: Mon Oct 20 13:25:01 2014
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_ChoosePortDialog(object):
    def setupUi(self, ChoosePortDialog):
        ChoosePortDialog.setObjectName(_fromUtf8("ChoosePortDialog"))
        ChoosePortDialog.resize(400, 300)
        self.verticalLayout = QtGui.QVBoxLayout(ChoosePortDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.error = QtGui.QLabel(ChoosePortDialog)
        self.error.setStyleSheet(_fromUtf8("font-weight: bold;"))
        self.error.setObjectName(_fromUtf8("error"))
        self.verticalLayout.addWidget(self.error)
        self.message = QtGui.QLabel(ChoosePortDialog)
        self.message.setObjectName(_fromUtf8("message"))
        self.verticalLayout.addWidget(self.message)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(ChoosePortDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.port = QtGui.QLineEdit(ChoosePortDialog)
        self.port.setMaxLength(5)
        self.port.setObjectName(_fromUtf8("port"))
        self.horizontalLayout.addWidget(self.port)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.buttonBox = QtGui.QDialogButtonBox(ChoosePortDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Abort|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(ChoosePortDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ChoosePortDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ChoosePortDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ChoosePortDialog)

    def retranslateUi(self, ChoosePortDialog):
        ChoosePortDialog.setWindowTitle(_translate("ChoosePortDialog", "Dialog", None))
        self.error.setText(_translate("ChoosePortDialog", "<error>", None))
        self.message.setText(_translate("ChoosePortDialog", "Choose port for the message server\n"
"( 0 for automatic assignement )", None))
        self.label.setText(_translate("ChoosePortDialog", "Port: ", None))
        self.port.setText(_translate("ChoosePortDialog", "0", None))

