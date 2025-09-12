def from_ascii(raw_string: str):  # necessary for nonstandard unit characters, e.g. mu
    if raw_string == "":
        return ""
    return raw_string.encode("ascii").decode("unicode_escape")


def to_ascii(val):  # encoding is necessary for exporting image metadata
    if val == "":
        return ""
    return val.encode("unicode_escape").decode("ascii")


def to_ome(val):
    if val.lower() in ome_units:
        return ome_units[val.lower()]
    return "pixel"


ome_units = {
    "pixel": "pixel",
    "": "pixel",
    "kilometer": "km",
    "kilometers": "km",
    "km": "km",
    "meter": "m",
    "meters": "m",
    "m": "m",
    "centimeter": "cm",
    "centimeters": "cm",
    "cm": "cm",
    "millimeter": "mm",
    "millimeters": "mm",
    "mm": "mm",
    "micrometer": "µm",
    "micrometers": "µm",
    "um": "µm",
    "μm": "µm",
    "µm": "µm",
    "micron": "µm",
    "microns": "µm",
    "nanometer": "nm",
    "nanometers": "nm",
    "nm": "nm",
    "picometer": "pm",
    "picometers": "pm",
    "pm": "pm",
    "femtometer": "fm",
    "femtometers": "fm",
    "fm": "fm",
    "sec": "s",
    "secs": "s",
    "seconds": "s",
    "s": "s",
    "millisecond": "ms",
    "milliseconds": "ms",
    "ms": "ms",
}
