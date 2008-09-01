"""
paste app factory
"""
from paste.httpexceptions import HTTPExceptionHandler
from traclegos.web import View

def make_app(global_conf, **app_conf):
    """create the traclegos view and wrap it in middleware"""
    key_str = 'traclegos.'
    args = dict([(key.split(key_str, 1)[-1], value)
                 for key, value in app_conf.items()
                 if key.startswith(key_str) ])
    app = View(**args)
    return HTTPExceptionHandler(app)
