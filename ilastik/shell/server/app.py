from apistar.frameworks.wsgi import WSGIApp as App
from apistar import Route, Include
from apistar.handlers import docs_urls, static_urls

from .routes import basic
from .ilastikAPI import IlastikAPI
from .renderer import IlastikJSONRenderer


routes = [
    Include('/docs', docs_urls),
    Include('/static', static_urls)
]

# extend here in order to add them to site root
routes.extend(basic.routes)

settings = {
    'RENDERERS': [IlastikJSONRenderer()],
    'SCHEMA': {
        'TITLE': "ilastik-API",
        'DESCRIPTION': "ilastiks http intrerface for third party applications."
    }
}


app = App(routes=routes, settings=settings)

ilastik_api = IlastikAPI()
app._ilastik_api = ilastik_api

if __name__ == '__main__':
    app.main()
