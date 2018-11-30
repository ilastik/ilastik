from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QLineEdit

from tiktorch.build_spec import TikTorchSpec, BuildSpec
import yaml


class QIComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(QIComboBox, self).__init__(parent)


class MagicWizard(QtWidgets.QWizard):
    def __init__(self, parent=None):
        super(MagicWizard, self).__init__(parent)
        self.addPage(Page1(self))
        self.setWindowTitle("Tiktorch Object Build Wizard")
        self.resize(640, 480)
        self.setOption(self.NoBackButtonOnStartPage)
        # self.setOption(self.HaveHelpButton)
        # self.button(QWizard.HelpButton).clicked.connect(self.showhelp())

class Page1(QtWidgets.QWizardPage):
    def __init__(self, parent=None):
        super(Page1, self).__init__(parent)

        self.label1 = QtWidgets.QLabel()

        self.code_path_textbox = QLineEdit(self)
        self.code_path_textbox.setPlaceholderText("Path to the .py file where the model lives")

        self.model_class_name_textbox = QLineEdit(self)
        self.model_class_name_textbox.setPlaceholderText("Name of the model class in the .py file")

        self.state_path_textbox = QLineEdit(self)
        self.state_path_textbox.setPlaceholderText("Path to where the state_dict is pickled")

        self.input_shape_textbox = QLineEdit(self)
        self.input_shape_textbox.setPlaceholderText("Input shape of the model as tuple/list ('CHW'/'CDHW')")

        self.minimal_increment_textbox = QLineEdit(self)
        self.minimal_increment_textbox.setPlaceholderText("Minimal values by which to increment/decrement the input shape to be still valid as tuple/list ('HW'/'DHW')")

        self.model_init_kwargs_textbox = QLineEdit(self)
        self.model_init_kwargs_textbox.setPlaceholderText("Kwargs to the model constructor (Optional)")

        self.model_path_textbox = QLineEdit(self)
        self.model_path_textbox.setPlaceholderText("Path were this configuration will be saved")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label1)
        layout.addWidget(self.code_path_textbox)
        layout.addWidget(self.model_class_name_textbox)
        layout.addWidget(self.state_path_textbox)
        layout.addWidget(self.input_shape_textbox)
        layout.addWidget(self.minimal_increment_textbox)
        layout.addWidget(self.model_init_kwargs_textbox)
        layout.addWidget(self.model_path_textbox)
        self.setLayout(layout)

    def initializePage(self):
        self.label1.setText("Parameters for TikTorch configuration:")

    def validatePage(self):
        # will be triggered after pressing Done
        self.saveParameters()
        return True

    def saveParameters(self):
        """
        Saves the parameters as tiktorch Object
        """
        self.code_path = str(self.code_path_textbox.text())
        self.model_class_name = str(self.model_class_name_textbox.text())
        self.state_path = str(self.state_path_textbox.text())
        self.input_shape = [int(x) for x in self.input_shape_textbox.text()[1:-1].replace(', ', ',').split(',')]
        self.minimal_increment = [int(x) for x in self.minimal_increment_textbox.text()[1:-1].replace(', ',',').split(',')]
        self.model_init_kwargs = yaml.load(str(self.model_init_kwargs_textbox.text())[1:-1].replace(', ', '\n'))
        self.model_path = str(self.model_path_textbox.text())

        spec = TikTorchSpec(
            code_path=self.code_path,
            model_class_name=self.model_class_name,
            state_path=self.state_path,
            input_shape=self.input_shape,
            minimal_increment=self.minimal_increment,
            model_init_kwargs=self.model_init_kwargs,
        )

        buildface = BuildSpec(self.model_path)
        buildface.build(spec)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    wizard = MagicWizard()
    wizard.show()
    sys.exit(app.exec_())
