import vigra
import json

from vigra import AxisType

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


class UnitAxisInfo(vigra.AxisInfo):
    def __init__(self, key="?", typeFlags=AxisType.UnknownAxisType, resolution=0.0, description="", unit=""):
        super().__init__(key, typeFlags, resolution, description)
        self.unit = unit


class UnitAxisTags(vigra.AxisTags):
    def toJSON(self):
        return json.dumps(
            {
                "axes": [
                    {
                        "key": tag.key,
                        "type": str(tag.typeFlags),
                        "description": tag.description,
                        "resolution": tag.resolution,
                        "unit": tag.unit if isinstance(tag, UnitAxisInfo) else "",
                    }
                    for tag in self
                ]
            }
        )

    @staticmethod
    def fromJSON(json_str):
        data = json.loads(json_str)

        if all(info["unit"] == "" for info in data["axes"]):
            return super().fromJSON(json_str)

        return UnitAxisTags([UnitAxisInfo(**info_dict) for info_dict in data["axes"]])

    def __copy__(self):
        new = type(self)(self)
        new.unit_tags = self.unit_tags
        return new
