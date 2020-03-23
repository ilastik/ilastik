from collections.abc import Mapping


def is_value(value):
    if isinstance(value, Mapping):
        return False
    if hasattr(value, "__iter__") and not isinstance(value, (str, bytes, bytearray)):
        return False
    return True


def flatten(d: dict):
    out_dict = {}
    for k, v in d.items():
        if is_value(v):
            out_dict[str(k)] = v
        else:
            if isinstance(v, Mapping):
                pairs = flatten(v).items()
            else:
                pairs = flatten(dict(enumerate(v))).items()
            for k2, v2 in pairs:
                out_dict[f"{k}.{k2}"] = v2
    return out_dict


def is_int(key):
    try:
        _ = int(key)
        return True
    except ValueError:
        return False


def listify(value):
    if is_value(value):
        return value
    if isinstance(value, Mapping):
        if len(value) > 0 and all(is_int(k) for k in value.keys()):
            l = []
            for k in value.keys():
                l.insert(int(k), listify(value[k]))
            return l
        else:
            return {k: listify(v) for k, v in value.items()}
    return [listify(item) for item in value]


def unflatten(d: dict):
    out_dict = {}
    for k, v in d.items():
        key_parts = k.split(".")
        obj = out_dict
        for part in key_parts[:-1]:
            if part not in obj:
                obj[part] = {}
            obj = obj[part]
        obj[key_parts[-1]] = v
    return out_dict
