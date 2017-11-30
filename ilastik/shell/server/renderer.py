import json
from apistar.renderers import Renderer
from apistar import http


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        # check if object has to_json() method
        if hasattr(obj, 'to_json'):
            return obj.to_json()

        return json.JSONEncoder.default(self, obj)


class IlastikJSONRenderer(Renderer):
    def render(self, data: http.ResponseData) -> bytes:
        return json.dumps(data, cls=CustomEncoder).encode('utf-8')
