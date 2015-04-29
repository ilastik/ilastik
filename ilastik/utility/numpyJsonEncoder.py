import json
import numpy


class NumpyJsonEncoder(json.JSONEncoder):
    """
    json.dumps cannot encode numpy's dtypes
    with json.dumps(string, cls=NumpyJsonEncode) it can
    """
    def default(self, obj):
        if type(obj).__module__ == numpy.__name__:
            try:
                return obj.tolist()
            except (ValueError, AttributeError):
                raise RuntimeError("Could not encode Numpy type: {}".format(type(obj)))
        return super(json.JSONEncoder, self).default(obj)