from pkg_resources import Requirement, resource_string

_variables = None

def get_global_configurations(variable_name=None):
    """
    Reads the plugin configuration file and returns all the values 
    in a dictionary or the variable_name passed as parameter.
    
    @param variable_name: String
    """
    global _variables
    if _variables is not None :
        if _variables.has_key(variable_name) :
            return _variables[variable_name]
    global_conf = resource_string(Requirement.parse("TracSVNPoliciesPlugin"), '/svnpolicies/svnpolicy.conf')
    prev = locals().copy()
    exec(global_conf)
    next = locals().copy()
    next.pop('prev')
    _variables={}
    for value_name in next.keys() :
        if not prev.has_key(value_name):
            _variables[value_name] = next[value_name]
    if variable_name is not None:
        if _variables.has_key(variable_name) :
            return _variables[variable_name]
    return _variables


production= True
try :
    from svnpolicies import api
except Exception :
    import site
    site.addsitedir(get_global_configurations('PYTHON_SITE_DIR'))
    production= True
    from svnpolicies import api

AUTHOR_URL_TEMPLATE= get_global_configurations('AUTHOR_URL_TEMPLATE');
CHANGESET_URL= get_global_configurations('CHANGESET_URL');
SVNNOTIFY= get_global_configurations('SVNNOTIFY');
SVNLOOK= get_global_configurations('SVNLOOK');
SMTP_HOST= get_global_configurations('SMTP_HOST');
SMTP_USER= get_global_configurations('SMTP_USER');
SMTP_PASSWORD= get_global_configurations('SMTP_PASSWORD');
CREDENTIALS= "-S" + \
            " --smtp " + SMTP_HOST + \
            " --smtp-user " + SMTP_USER + \
            " --smtp-password " + SMTP_PASSWORD

PYTHONPATH= get_global_configurations('PYTHON_SITE_DIR')

TRAC_CODE_PATH=get_global_configurations('TRAC_CODE_PATH');

