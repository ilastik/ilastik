 
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtCore import pyqtProperty
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QLineEdit

from tiktorch.buildy import TikTorchSpec, BuildyMcBuildface
import numpy as np
import yaml
 
class QIComboBox(QtWidgets.QComboBox):
    def __init__(self,parent=None):
        super(QIComboBox, self).__init__(parent)
 
 
class MagicWizard(QtWidgets.QWizard):
    def __init__(self, parent=None):
        super(MagicWizard, self).__init__(parent)
        self.addPage(Page1(self))
        self.setWindowTitle("Tiktorch Object Build Wizard")
        self.resize(640,480)
 
class Page1(QtWidgets.QWizardPage):
    def __init__(self, parent=None):
        super(Page1, self).__init__(parent)

        self.label1 = QtWidgets.QLabel()

        self.code_path_textbox = QLineEdit(self)
        self.code_path_textbox.setPlaceholderText("Path to the .py file")

        self.model_class_name_textbox = QLineEdit(self)
        self.model_class_name_textbox.setPlaceholderText("Name of the model class in the .py file")

        self.state_path_textbox = QLineEdit(self)
        self.state_path_textbox.setPlaceholderText("Path to where the state_dict is pickled")

        self.input_shape_textbox = QLineEdit(self)
        self.input_shape_textbox.setPlaceholderText("Input shape of the model in the order CHW")

        self.output_shape_textbox = QLineEdit(self)
        self.output_shape_textbox.setPlaceholderText("Output shape of the model in the order CHW")

        self.dynamic_input_shape_textbox = QLineEdit(self)
        self.dynamic_input_shape_textbox.setPlaceholderText("dynamic_input_shape (Optional)")

        self.devices_textbox = QLineEdit(self)
        self.devices_textbox.setPlaceholderText("List of devices (e.g. 'cpu:0' or ['cuda:0', 'cuda:1'])")

        self.model_init_kwargs_textbox = QLineEdit(self)
        self.model_init_kwargs_textbox.setPlaceholderText("Kwargs to the model constructor (Optional)")

        self.model_path_textbox = QLineEdit(self)
        self.model_path_textbox.setPlaceholderText("Path were the object will be saved")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label1)
        layout.addWidget(self.code_path_textbox)
        layout.addWidget(self.model_class_name_textbox)
        layout.addWidget(self.state_path_textbox)
        layout.addWidget(self.input_shape_textbox)
        layout.addWidget(self.output_shape_textbox)
        layout.addWidget(self.dynamic_input_shape_textbox)
        layout.addWidget(self.devices_textbox)
        layout.addWidget(self.model_init_kwargs_textbox)
        layout.addWidget(self.model_path_textbox)
        self.setLayout(layout)

    def initializePage(self):
        self.label1.setText("Parameters:")

    def validatePage(self):
        #will be triggered after pressing Done
        self.saveParameters()
        return True


    def saveParameters(self):
        """
        Saves the parameters as tiktorch Object
        """
        self.code_path = str(self.code_path_textbox.text())
        self.model_class_name = str(self.model_class_name_textbox.text())
        self.state_path = str(self.state_path_textbox.text())
        self.input_shape = list(self.input_shape_textbox.text())
        self.output_shape = list(self.output_shape_textbox.text())
        self.dynamic_input_shape = str(self.dynamic_input_shape_textbox.text())
        self.devices = str(self.devices_textbox.text())
        self.model_init_kwargs = yaml.load(str(self.model_init_kwargs_textbox.text()))
        self.model_path = str(self.model_path_textbox.text())

        # self.input_shape = self.makeArray(self.input_shape)
        # self.output_shape = self.makeArray(self.output_shape)

        spec = TikTorchSpec(code_path=self.code_path, model_class_name=self.model_class_name, state_path=self.state_path,
                 input_shape=self.input_shape, output_shape=self.output_shape, dynamic_input_shape=self.dynamic_input_shape,
                 devices=self.devices, model_init_kwargs=self.model_init_kwargs)

        buildface = BuildyMcBuildface(self.model_path)
        buildface.build(spec)

    # def makeArray(self, input_str):
    #     """
    #     helper function for making an array out of the string
    #     """
    #     input_str = input_str.split(',')
    #     arr = np.zeros(3)
    #     for i,str in enumerate(input_str):
    #         arr[i] = int(str)

    #     return arr
 
if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    wizard = MagicWizard()
    wizard.show()
    sys.exit(app.exec_())