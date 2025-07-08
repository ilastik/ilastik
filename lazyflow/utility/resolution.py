import vigra
import json

"""
Subclass of VIGRA Axistags that handles an extra "units" field, allowing storage
and interpretation of pixel size data.

Methods
-------
getUnitTag(axis)
    Returns the unit string for the specified axis.
    :param axis: An axis key (e.g., "x", "t")
    :type axis: str
    :return: Unit string for the axis, or None if not set
    :rtype: str or None

getUnitDict()
    Returns a dictionary of units corresponding to axis keys.
    :return: Dictionary of (axis key, unit) pairs
    :rtype: dict

setUnitDict(units)
    Sets the unit dictionary.
    :param units: Dictionary of (axis key, unit) pairs
    :type units: dict
    :return: None

defaultUnitTags(axes)
    Returns the default unitTags for the specified axes.
    :param axes: String of axis keys (e.g. "txyc")
    :type axes: str
    :return: unitTags object
    :rtype: unitTags

toJSON()
    Converts the UnitTags object to a JSON-formatted string.
    :return: JSON string representation of the UnitTags object
    :rtype: str

fromJSON(json_string)
    Converts a JSON string into a unitTags object.
    :param json_string: JSON string representation of the unitTags object
    :type json_string: str
    :return: unitTags object
    :rtype: unitTags
"""


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
        new = type(self)(self)
        new.unit_tags = self.unit_tags
        return new
