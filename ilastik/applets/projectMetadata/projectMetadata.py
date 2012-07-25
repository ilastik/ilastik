import ilastik.utility

class ProjectMetadata(object):
    """
    Stores project metadata.
    Fires a signal if the metadata is changed.
    """
    def __init__(self):
        # This signal notifies subscribers that an item of metadata was changed
        self.changedSignal = ilastik.utility.SimpleSignal()

        self._projectName = ""
        self._labeler = ""
        self._description = ""

    @property
    def projectName(self):
        return self._projectName
    
    @projectName.setter
    def projectName(self, newProjectName):
        self._projectName = newProjectName
        self.changedSignal.emit()    

    @property
    def labeler(self):
        return self._labeler
    
    @labeler.setter
    def labeler(self, newLabeler):
        self._labeler = newLabeler
        self.changedSignal.emit()
        
    @property
    def description(self):
        return self._description
    
    @description.setter
    def description(self, newDescription):
        self._description = newDescription
        self.changedSignal.emit()
