# -*- coding: utf-8 -*-
#


from trac import config
from os import path
import re
from pkg_resources import Requirement, resource_string, resource_filename

all= ['IniReader', 
      'validate_email', 
      'get_global_configurations', 
      'get_resource_path', 
      'get_hook_path',
      'get_site_packages']

def get_site_packages():
    return path.sep.join(__file__.split(path.sep)[:-3])

def validate_email(email):
    """
    This function tries to validate a email address. 
    
    @param email: String
    @return: boolean
    """
    if len(email) > 7:
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
            return True
    return False


def get_global_configurations(variable_name=None):
    """
    Reads the plugin configuration file and returns all the values 
    in a dictionary or the variable_name passed as parameter.
    
    @param variable_name: String
    """
    global_conf = resource_string(Requirement.parse("TracSVNPoliciesPlugin"), '/svnpolicies/svnpolicy.conf')
    prev = locals().copy()
    exec(global_conf)
    next = locals().copy()
    next.pop('prev')
    return_dict={}
    for value_name in next.keys() :
        if not prev.has_key(value_name):
            return_dict[value_name] = next[value_name]
    if variable_name is not None:
        if return_dict.has_key(variable_name) :
            return return_dict[variable_name]
    return return_dict

def get_resource_path(resource_name):
    """
    """
    return resource_filename(Requirement.parse("TracSVNPoliciesPlugin"), resource_name)

def get_hook_path(hook_name):
    """
    """
    
    # exctract the loader and get the path
    loader_path =resource_filename(Requirement.parse("TracSVNPoliciesPlugin"), "/svnpolicies/hooks/loader.py" )
    hooks_directory = path.sep.join(loader_path.split(path.sep)[:-1])
    # write the packages.pth file
    pth_file = hooks_directory + path.sep + 'packages.pth'
    hook_file = hooks_directory + path.sep + hook_name
    if not path.isfile(pth_file) or not path.isfile(hook_file):
        sitepck_dir = get_site_packages()
        file_handler = file(pth_file,'w')
        file_handler.write(sitepck_dir)
        file_handler.close()
    
    # return the resource name
    return get_resource_path("/svnpolicies/hooks/" + hook_name)



class IniReader(object):
    """
    This class reads and offers api for accessing a trac environment
    ini file. 
    """
    _project_path= ""
    _project_name= ""
    _project_ini_file= ""
    _config= None
    
    def __init__(self, project_path):
        self._project_path= str(project_path)
        self._project_name= path.basename(project_path)
        self._project_ini_file= self._project_path + path.sep + "conf" + path.sep + "trac.ini"
        self._project_ini_file= path.normpath(self._project_ini_file)
        if path.isfile(self._project_ini_file) :
            self._config= config.Configuration(self._project_ini_file)
    
    def get_project_name(self):
        return self._project_name
    
    def get_project_path(self):
        return self._project_path
    
    def get_svn_policy_settings(self):
        """
        This method returns a dictionary from the settings that
        the admin has saved in the trac configuration file.
        This dictionary is used to create the hook files.
        
        @return: dict
        """
        return_dict = {'PROJECT' : ''}
        # the mail sender
        if self._config.getbool('svnpolicies', 'email.enabled') :
            return_dict['TO_LIST']= self._config.get('svnpolicies', 'email.list')
            return_dict['MAIL_SUBJECT']= self._config.get('svnpolicies', 'email.prefix')
            return_dict['MAIL_ATTACH']= self._config.getbool('svnpolicies', 'email.attachment')
            return_dict['MAIL_ATTACH_SIZE']= self._config.get('svnpolicies', 'email.attachment_limit')
            return_dict['MAIL_SUBJECT_CX']= self._config.getbool('svnpolicies', 'email_subject_cx')
            return_dict['MAIL_FROM']= self._config.getbool('svnpolicies', 'email_from_enabled')
            return_dict['MAIL_FROM_ADDRESS']= self._config.get('svnpolicies', 'email_from_address')
        # log message related
        if self._config.getbool('svnpolicies', 'log_message.required') :
            return_dict['LOG']= True
            return_dict['LOG_SIZE']= self._config.get('svnpolicies', 'log_message.minimum')
            return_dict['LOG_PATTERN']= self._config.get('svnpolicies', 'log_message.pattern')
        else :
            return_dict['LOG']= False
        # the log - command interpreter 
        if self._config.getbool('svnpolicies', 'commands.enabled') :
            return_dict['COMMANDS']= True
            return_dict['TRAC_CODE']= self._config.get('svnpolicies', 'trac_code')
        else :
            return_dict['COMMANDS']= False
        
        # advanced scripts
        if self._config.getbool('svnpolicies', 'advanced_precomit_enabled') :
            return_dict['ADVANCED_PRE']= True
            return_dict['ADVANCED_PRE_FILE']= self._config.get('svnpolicies', 'advanced_precomit_file')
        else :
            return_dict['ADVANCED_PRE']= False
            
        # advanced scripts
        if self._config.getbool('svnpolicies', 'advanced_postcomit_enabled') :
            return_dict['ADVANCED_POST']= True
            return_dict['ADVANCED_POST_FILE']= self._config.get('svnpolicies', 'advanced_postcomit_file')
        else :
            return_dict['ADVANCED_POST']= False
        
        if self._config.getbool('svnpolicies', 'svn_property') :
            return_dict['SVN_PROPERTY']= self._config.getbool('svnpolicies', 'svn_property')
        
        return_dict['READONLY']= self._config.getbool('svnpolicies', 'readonly_repository')
            
        
        return return_dict
    
    def get_svn_hook_path(self):
        """
        This method returns the path on the system where the
        svn server expects the hook file to be present. The trac 
        configuration file provides the svn repository information.
        
        @return: String
        If a error ocurs in the process of getting the path the method 
        returns None.
        """
        try :
            if self.config.get('trac', 'repository_type') == 'svn' :
                repository= self.config.get('trac', 'repository_dir')
                if path.isdir(repository) :
                    return str(repository) + '/hooks'
        except Exception:
            return None