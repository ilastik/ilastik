import vigra
import json


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

    def getUnitDict(self):
        return self.unit_tags

    def setUnitDict(self, dict):
        self.unit_tags = dict

    def setUnitTag(self, axis, tag):
        self.unit_tags[axis] = tag

    def defaultUnitTags(axes):
        return unitTags(vigra.defaultAxistags(axes))

    def toJSON(self):
        return json.dumps(
            {
                "axes": [
                    {
                        "key": tag.key,
                        "type": str(tag.typeFlags),
                        "description": tag.description,
                        "resolution": tag.resolution,
                        "unit": self.getUnitTag(tag.key),
                    }
                    for tag in self
                ]
            }
        )

    @staticmethod
    def fromJSON(json_str):
        data = json.loads(json_str)
        axes = "".join([axis["key"] for axis in data["axes"]])
        tags = unitTags(vigra.defaultAxistags(axes))
        for axiskey, selectedaxis in zip(axes, data["axes"]):
            tags.setResolution(axiskey, selectedaxis.get("resolution", 0))
            tags.setUnitTag(axiskey, selectedaxis.get("unit", None))
            tags.setDescription(axiskey, selectedaxis.get("description", ""))
        return tags

    def __copy__(self):
        # Create a new instance of UnitTags and copy the attributes
        new = type(self)(self)
        new.unit_tags = self.unit_tags
        return new
