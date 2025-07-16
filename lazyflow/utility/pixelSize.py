import vigra
import json

from typing import Dict, Union
from vigra import AxisType


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
