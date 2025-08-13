def fromASCII(raw_string: str):  # necessary for nonstandard unit characters, e.g mu
    return raw_string.encode("utf-8").decode("unicode_escape").encode("utf-16", "surrogatepass").decode("utf-16")


def toASCII(val):  # encoding is necessary for exporting image metadata
    return val.encode("unicode_escape").decode("ascii")
