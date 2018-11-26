###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
import sys
import os
import yaml
from tiktorch.build_spec import BuildSpec, TikTorchSpec
from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QApplication, QGridLayout, QLabel, QLineEdit, QWidget, QFileDialog, QWizard, QDesktopWidget, QMainWindow


class HyperparameterGui(QWidget):
    def __init__(self, topLevelOperator):
        super(HyperparameterGui, self).__init__()
        self.topLevelOperator = topLevelOperator
        
        self.initUI()

    def initUI(self):
        self.learning_rate_textbox = QLineEdit()
        self.learning_rate_textbox.setPlaceholderText("default: 0.001")
        self.iterations_textbox = QLineEdit()
        self.iterations_textbox.setPlaceholderText("default: 1000 iterations")
        self.weight_decay_textbox = QLineEdit()
        self.weight_decay_textbox.setPlaceholderText("default: 0.005")
        #self.code_path_textbox = QLineEdit()
        #self.code_path_textbox.setPlaceholderText("Path to the hyperparameter file")

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel('Learning Rate'), 1, 0)
        grid.addWidget(self.learning_rate_textbox, 1, 1)

        grid.addWidget(QLabel('Number of Iterations'), 2, 0)
        grid.addWidget(self.iterations_textbox, 2, 1)

        grid.addWidget(QLabel('Weight Decay'), 3, 0)
        grid.addWidget(self.weight_decay_textbox, 3, 1)

        #grid.addWidget(self.code_path_textbox, 4, 0, 4, 2)

        okButton = QPushButton("OK")
        okButton.clicked.connect(self.saveParameters)
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.close)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(okButton)
        hbox.addWidget(cancelButton)

        vbox = QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

        #self.resize(480, 200)
        self.setFixedSize(480, 180)
        self.center()
        
        self.setWindowTitle('Hyperparameter Settings')
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def saveParameters(self):
        #self.code_path = str(self.code_path_textbox.text()) if len(self.code_path_textbox.text()) > 0 else '/home/jo/'
        self.learning_rate = float(self.learning_rate_textbox.text()) if len(self.learning_rate_textbox.text()) > 0 else 0.001
        self.iterations = int(self.iterations_textbox.text()) if len(self.iterations_textbox.text()) > 0 else 1000
        self.weight_decay = float(self.weight_decay_textbox.text()) if len(self.weight_decay_textbox.text()) > 0 else 0.005

        config_dict = {'learning_rate': self.learning_rate,
                       'iterations': self.iterations,
                       'weight_decay': self.weight_decay}

        options = QFileDialog.Options(QFileDialog.ShowDirsOnly)
        folder_name = QFileDialog.getExistingDirectory(self, "Select where to store hyperparameter config",
                                                       os.path.expanduser('~'), options)
        file_name = 'tiktorch_hyperparameter_config.yml'
        dump_file_name = os.path.join(folder_name, file_name)
        
        with open(dump_file_name, 'w') as f:
            yaml.dump(config_dict, f)

        #self.topLevelOperator.HyperparametersPath.setValue(dump_file_name)
        self.close()


class CreateTikTorchModelGui(QWidget):
    def __init__(self, topLevelOperator):
        super(CreateTikTorchModelGui, self).__init__()
        self.topLevelOperator = topLevelOperator
        
        self.initUI()

    def initUI(self):
        self.codePathTextbox = QLineEdit()
        self.codePathTextbox.setPlaceholderText("Path to the .py file where the model lives.")
        self.modelNameTextbox = QLineEdit()
        self.modelNameTextbox.setPlaceholderText("Name of the model class in the code path.")
        self.statePathTextbox = QLineEdit()
        self.statePathTextbox.setPlaceholderText("Path to where the state_dict is pickled.")
        self.inputShapeTextbox = QLineEdit()
        self.inputShapeTextbox.setPlaceholderText("Input shape of the model. Must be 'CHW' (for 2D models) or 'CDHW' (for 3D models). (tuple / list)")
        self.minimalIncrementTextbox = QLineEdit()
        self.minimalIncrementTextbox.setPlaceholderText("Minimal values by which to increment / decrement the input shape for it to still be valid. (tuple / list)")
        self.modelKwargsTextbox = QLineEdit()
        self.modelKwargsTextbox.setPlaceholderText("Keywords to the model constructor (if any). (dict)")
        self.descriptionTextbox = QLineEdit()
        self.descriptionTextbox.setPlaceholderText("Description of the pre-trained mode. (Optional)")
        self.dataSourceTextbox = QLineEdit()
        self.dataSourceTextbox.setPlaceholderText("url to data used for pre-training. (Optional)")

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel('Code Path'), 1, 0)
        grid.addWidget(self.codePathTextbox, 1, 1)

        grid.addWidget(QLabel('Model Name'), 2, 0)
        grid.addWidget(self.modelNameTextbox, 2, 1)

        grid.addWidget(QLabel('State Path'), 3, 0)
        grid.addWidget(self.statePathTextbox, 3, 1)

        grid.addWidget(QLabel('Input Shape'), 4, 0)
        grid.addWidget(self.inputShapeTextbox, 4, 1)

        grid.addWidget(QLabel('Minimal Increment'), 5, 0)
        grid.addWidget(self.minimalIncrementTextbox, 5, 1)

        grid.addWidget(QLabel('Keyword Arguments'), 6, 0)
        grid.addWidget(self.modelKwargsTextbox, 6, 1)

        grid.addWidget(QLabel('Description'), 7, 0)
        grid.addWidget(self.descriptionTextbox, 7, 1)

        grid.addWidget(QLabel('Data Source'), 8, 0)
        grid.addWidget(self.dataSourceTextbox, 8, 1)

        okButton = QPushButton("OK")
        okButton.clicked.connect(self.saveParameters)
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.close)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(okButton)
        hbox.addWidget(cancelButton)

        vbox = QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

        #self.resize(480, 200)
        self.setFixedSize(500, 380)
        self.center()
        
        self.setWindowTitle('Create TikTorch Model')
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def saveParameters(self):
        print(type(self.inputShapeTextbox.text()))
        print(tuple(str(self.inputShapeTextbox.text())))
        spec = TikTorchSpec(code_path=str(self.codePathTextbox.text()),
                            model_class_name=str(self.modelNameTextbox.text()),
                            state_path=str(self.statePathTextbox.text()),
                            input_shape=(1, 572, 572),
                            minimal_increment=[32, 32],
                            model_init_kwargs={'in_channels': 1, 'out_channels': 1, 'initial_features': 64})
        self.spec.validate()
        build_spec = BuildSpec(build_directory='/home/jo/ISBI_UNet_pretrained', device='cpu')
        build_spec.build(self.spec)
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = HyperparameterGui()
    sys.exit(app.exec_())
