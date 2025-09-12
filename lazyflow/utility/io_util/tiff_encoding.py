def from_ascii(raw_string: str):  # necessary for nonstandard unit characters, e.g. mu
    if raw_string == "":
        return ""
    return raw_string.encode("ascii").decode("unicode_escape")
