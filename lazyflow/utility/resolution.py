import vigra


class resAxisInfo(vigra.AxisInfo):
    def __init__(self, key, resolution, unit, description):
        super().__init__(key, resolution, description)
        self.units = unit


class unitTags(vigra.AxisTags):
    def __init__(self, axes=""):
        super().__init__(axes)
        self.unit_tags = {}

    def getUnitTag(self, axis):
        if axis in self.unit_tags.keys():
            return self.unit_tags[axis]
        else:
            return None

    def setUnitTag(self, axis, tag):
        self.unit_tags[axis] = tag

    def defaultUnitTags(axes):
        return unitTags(vigra.defaultAxistags(axes))

    def __copy__(self):
        # Create a new instance of UnitTags and copy the attributes
        new = type(self)(self)
        new.unit_tags = self.unit_tags
        return new
