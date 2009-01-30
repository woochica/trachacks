"""
paste app factory
"""
from paste.httpexceptions import HTTPExceptionHandler
from traclegos.web import View

def str2list(string):
    """returns a list from a comma-separated string"""
    # XXX this could go in a utils.py file
    return [ i.strip() for i in string.split(',') if i.strip() ]

def make_app(global_conf, **app_conf):
    """create the traclegos view and wrap it in middleware"""
    key_str = 'traclegos.'

    # constructor arguments
    list_items = [ 'conf', 'site_templates', 
                   'available_templates', 'available_repositories',
                   'available_databases' ]
    args = dict([(key.split(key_str, 1)[-1], value)
                 for key, value in app_conf.items()
                 if key.startswith(key_str) ])
    for item in list_items:
        if args.has_key(item):
            args[item] = str2list(args[item])

    # variables
    args['variables'] = dict([(key.split(key_str, 1)[-1], value)
                              for key, value in global_conf.items()
                              if key.startswith(key_str) ])
    app = View(**args)
    return HTTPExceptionHandler(app)
