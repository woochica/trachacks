
import os

_variables = None

def get_real_path(link, cut_by=2):
    """
    This function determines the real file that hides under symlinks.
    
    @return: String
    @param link: String
    """
    hook_file= os.path.realpath(link)
    return os.path.sep.join(hook_file.split(os.path.sep)[:-cut_by])

def get_trac_path(link, cut_by=2):
    """
    This function determines the target of a symlink.
    
    @return: String
    @param link: String
    """
    hook_file= os.readlink(link)
    return os.path.sep.join(hook_file.split(os.path.sep)[:-cut_by])

PYTHONPATH = ''
production= False
try :
    from svnpolicies import api
except Exception :
    import site
    # get the python path from the pth file
    pth_handle = file(get_real_path(__file__, 1) + os.sep +'packages.pth','r')
    PYTHONPATH = pth_handle.readline().strip()
    pth_handle.close()
    # load it
    site.addsitedir(PYTHONPATH)
    production= True
    from svnpolicies import api

AUTHOR_URL_TEMPLATE = api.get_global_configurations('AUTHOR_URL_TEMPLATE');
CHANGESET_URL = api.get_global_configurations('CHANGESET_URL');
SVNNOTIFY = api.get_global_configurations('SVNNOTIFY');
SVNLOOK = api.get_global_configurations('SVNLOOK');
SMTP_HOST = api.get_global_configurations('SMTP_HOST');
SMTP_USER = api.get_global_configurations('SMTP_USER');
SMTP_PASSWORD = api.get_global_configurations('SMTP_PASSWORD');
CREDENTIALS = "-S" + \
            " --smtp " + SMTP_HOST + \
            " --smtp-user " + SMTP_USER + \
            " --smtp-password " + SMTP_PASSWORD

TRAC_CODE_PATH = api.get_global_configurations('TRAC_CODE_PATH');

