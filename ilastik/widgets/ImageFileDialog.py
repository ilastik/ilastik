import os
from typing import List
from pathlib import Path

from PyQt5.QtWidgets import QFileDialog

from volumina.utility import PreferencesManager
from ilastik.applets.dataSelection.opDataSelection import OpDataSelection
from ilastik.config import cfg as ilastik_config


class ImageFileDialog(QFileDialog):
    def __init__(
        self,
        parent_window,
        preferences_group: str = "DataSelection",
        preferences_setting: str = "recent image",
        preferences_manager: PreferencesManager = PreferencesManager(),
    ):
        self.preferences_group = preferences_group
        self.preferences_setting = preferences_setting
        self.preferences_manager = preferences_manager
        # Find the directory of the most recently opened image file
        mostRecentImageFile = preferences_manager.get(preferences_group, preferences_setting)
        if mostRecentImageFile is None:
            defaultDirectory = os.path.expanduser("~")
        else:
            defaultDirectory = os.path.dirname(str(mostRecentImageFile))

        extensions = OpDataSelection.SupportedExtensions
        ext_str = " ".join(f"*.{ext} (*.{ext})" for ext in extensions)
        filters = f"Image files ({ext_str})"

        super().__init__(parent_window, caption="Select Images", directory=defaultDirectory, filter=filters)
        self.setFileMode(QFileDialog.ExistingFiles)

    def getSelectedPaths(self) -> List[Path]:
        if not super().exec_():
            return []
        self.preferences_manager.set(self.preferences_group, self.preferences_setting, self.selectedFiles()[0])
        filePaths = []
        for selected_file in self.selectedFiles():
            path = Path(selected_file)
            if path.name.lower() == "attributes.json" and any(p.suffix.lower() == ".n5" for p in path.parents):
                # For the n5 extension the attributes.json file has to be selected in the file dialog.
                # However we need just the *.n5 directory-file.
                filePaths.append(path.parent)
            else:
                filePaths.append(path)
        return filePaths
