import os
from typing import List
from pathlib import Path

from PyQt5.QtWidgets import QFileDialog

from volumina.utility import PreferencesManager
from .opDataSelection import OpDataSelection, DatasetInfo
from ilastik.config import cfg as ilastik_config

class ImageFileDialog(QFileDialog):
    def __init__(self, parent_window):
        # Find the directory of the most recently opened image file
        mostRecentImageFile = PreferencesManager().get('DataSelection', 'recent image' )
        mostRecentImageFile = str(mostRecentImageFile)
        if mostRecentImageFile is not None:
            defaultDirectory = os.path.split(mostRecentImageFile)[0]
        else:
            defaultDirectory = os.path.expanduser('~')

        extensions = OpDataSelection.SupportedExtensions
        filter_strs = ["*." + x for x in extensions]
        filters = [f"{filt} ({filt})" for filt in filter_strs]
        filt_all_str = "Image files (" + ' '.join(filter_strs) + ')'

        super().__init__(parent_window, caption="Select Images",
                         directory=defaultDirectory, filter=filt_all_str)
        # use Qt dialog in debug mode (more portable?)
        self.setOption(QFileDialog.DontUseNativeDialog, ilastik_config.getboolean("ilastik", "debug"))
        self.setFileMode(QFileDialog.ExistingFiles)

    def getSelectedPaths(self) -> List[Path]:
        if not super().exec_():
            return []
        filePaths = [Path(selected_file) for selected_file in self.selectedFiles()]
        PreferencesManager().set('DataSelection', 'recent image', filePaths[0].as_posix())#FIXME: use platform style, maybe?
        # For the n5 extension the attributes.json file has to be selected in the file dialog.
        # However we need just the *.n5 directory-file.
        for i, path in enumerate(filePaths):
            if path.name.lower() == 'attributes.json' and any(p.suffix.lower() == ".n5" for p in filePath.parents):
                filePaths[i] = filePath.parent
        return filePaths


