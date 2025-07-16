from typing import Dict, Union

import vigra
import json

from vigra import AxisType

"""
Subclass of VIGRA Axistags that handles an extra "units" field within UnitAxisInfo (subclass of AxisInfo), allowing storage
and interpretation of pixel size data.

Methods
-------

defaultUnitAxisTags(axes)
    Returns the default unitTags for the specified axes.
    :param axes: String of axis keys (e.g. "txyc")
    :type axes: str
    :return: unitAxisTags object
    :rtype: unitAxisTags

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
        if (
            abs(resolution - round(resolution)) < 0.001
        ):  # this might need removing depending on views on floating-point division
            resolution = round(resolution)
        super().__init__(key, typeFlags, resolution, description)
        if isinstance(unit, str) and unit.startswith("('") and unit.endswith("',)"):
            unit = unit[2:-3]
        self.unit = unit

    def __copy__(self):
        return UnitAxisInfo(
            key=self.key,
            typeFlags=self.typeFlags,
            resolution=self.resolution,
            description=self.description,
            unit=self.unit,
        )


class UnitAxisTags(vigra.AxisTags):

    def __init__(self, infos=None):
        super().__init__(infos)
        self._unit_dict = {}
        if infos is not None:
            if isinstance(infos, (list, tuple)):
                for info in infos:
                    if hasattr(info, "unit"):
                        self._unit_dict[info.key] = info.unit
            elif isinstance(infos, vigra.AxisTags):
                for key in infos.keys():
                    info = infos[key]
                    if hasattr(info, "unit"):
                        self._unit_dict[key] = info.unit

    def __getitem__(self, key):
        try:
            value = super().__getitem__(key)
            unit = self._unit_dict[value.key] if value.key in self._unit_dict else ""
            return UnitAxisInfo(
                key=value.key,
                typeFlags=value.typeFlags,
                resolution=value.resolution,
                description=value.description,
                unit=unit,
            )
        except (RuntimeError, IndexError, KeyError) as e:
            # if the key doesn't exist create a default unitaxisinfo
            if isinstance(key, str):
                # determine the appropriate typeflag based on the key
                if key.lower() in ["x", "y", "z"]:
                    type_flags = AxisType.Space
                elif key.lower() == "t":
                    type_flags = AxisType.Time
                elif key.lower() == "c":
                    type_flags = AxisType.Channels
                else:
                    type_flags = AxisType.UnknownAxisType
                return UnitAxisInfo(key=key, typeFlags=type_flags, resolution=0.0, description="", unit="")
            else:
                raise

    def setUnit(self, axis, unit):
        self[axis].unit = unit

    @staticmethod
    def defaultUnitAxisTags(axes):
        def_axes = vigra.defaultAxistags(axes)
        axis_infos = []
        for axis in def_axes.keys():
            in_info = def_axes[axis]
            axis_infos.append(UnitAxisInfo(axis, in_info.typeFlags, in_info.resolution, in_info.description, ""))

        return UnitAxisTags(axis_infos)

    @staticmethod
    def mapTypeFlag(flag):
        if flag == "Space":
            return 2
        elif flag == "Time":
            return 8
        elif flag == "Channels":
            return 1
        else:
            return 0

    def toJSON(self):
        return json.dumps(
            {
                "axes": [
                    {
                        "key": tag.key,
                        "typeFlags": UnitAxisTags.mapTypeFlag(str(tag.typeFlags)),
                        "resolution": tag.resolution,
                        "description": tag.description,
                        "unit": tag.unit if isinstance(tag, UnitAxisInfo) else "",
                    }
                    for tag in self
                ]
            }
        )

    @staticmethod
    def fromJSON(json_str):
        data = json.loads(json_str)

        axis_type_map = {
            "Space": AxisType.Space,
            "Time": AxisType.Time,
            "Frequency": AxisType.Frequency,
            "Angle": AxisType.Angle,
            "Channels": AxisType.Channels,
            "Edge": AxisType.Edge,
            "UnknownAxisType": AxisType.UnknownAxisType,
        }
        axis_infos = []
        for info_dict in data["axes"]:
            key = info_dict["key"]
            type_str = info_dict.get("typeFlags", "UnknownAxisType")
            try:
                type_int = int(type_str)
                if type_int == 2:
                    type_flags = AxisType.Space
                elif type_int == 8:
                    type_flags = AxisType.Time
                elif type_int == 1:
                    type_flags = AxisType.Channels
            except ValueError:
                # i.e. not in integer format
                type_flags = axis_type_map.get(type_str, AxisType.UnknownAxisType)

            resolution = info_dict.get("resolution", 0.0)
            description = info_dict.get("description", "")
            unit = info_dict.get("unit", "")

            axis_infos.append(UnitAxisInfo(key, type_flags, resolution, description, unit))

        return UnitAxisTags(axis_infos)

    def __copy__(self):
        out_infos: Dict[str, Union[UnitAxisInfo, vigra.AxisInfo]] = {}

        for axis in self.keys():
            in_info = self[axis]
            out_infos[axis] = UnitAxisInfo(
                key=axis,
                typeFlags=in_info.typeFlags,
                resolution=in_info.resolution,
                description=in_info.description,
                unit=in_info.unit,
            )

        new = UnitAxisTags([out_infos[key] for key in self.keys()])
        return new
