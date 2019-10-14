import os
from typing import List
from pathlib import Path

from PyQt5.QtWidgets import QFileDialog

from volumina.utility import preferences
from ilastik.applets.dataSelection.opDataSelection import OpDataSelection


class ImageFileDialog(QFileDialog):
    def __init__(
        self,
        parent_window,
        preferences_group: str = "DataSelection",
        preferences_setting: str = "recent image",
    ):
        self.preferences_group = preferences_group
        self.preferences_setting = preferences_setting

        ext_str = " ".join(f"*.{ext}" for ext in OpDataSelection.SupportedExtensions)
        filters = f"Image files ({ext_str})"
        # empty QFileDialog.Options() need to be provided, otherwise native dialog is not shown
        super().__init__(
            parent_window,
            caption="Select Images",
            directory=str(Path(preferences.get(preferences_group, preferences_setting, Path.home()))),
            filter=filters,
            options=QFileDialog.Options(),
        )
        self.setFileMode(QFileDialog.ExistingFiles)

    def getSelectedPaths(self) -> List[Path]:
        if not super().exec_():
            return []
        preferences.set(self.preferences_group, self.preferences_setting, Path(self.selectedFiles()[0]).as_posix())
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
