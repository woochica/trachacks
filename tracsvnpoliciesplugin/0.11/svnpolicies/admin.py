# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Optaros, Inc.
# All rights reserved.
#

import os
import stat
import traceback
import re
from os import path

from trac.core import implements, Component
from trac.config import Option, ListOption, BoolOption
from trac.admin.api import IAdminPanelProvider
from trac.util.translation import _
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.wiki.formatter import wiki_to_html

from svnpolicies import api

class SVNPoliciesAdminPlugin(Component):
    """ 
    This Admin panel enables a PROJECT_ADMIN user to configure policies
    regarding the usage of SVN for the project.  The SVN policies are 
    implemented as hooks.
    """
    action_status= None
    valid_email_flag = None
    errors= False
    
    implements(IAdminPanelProvider, ITemplateProvider)
    
    svnpolicies_enabled = BoolOption('svnpolicies', 'svnpolicies_enabled', 'false',
      "Enable the svnpolicies plugin")
    email_enabled = BoolOption('svnpolicies', 'email.enabled', 'false',
      "Enable email notifications")
    email_list =  ListOption('svnpolicies', 'email.list', '',
      "Comma seprated list of email recipients")
    email_from_enabled = BoolOption('svnpolicies', 'email_from_enabled', 'false',
      "Enable one address email for all the emails sent.")
    email_from_address =  Option('svnpolicies', 'email_from_address', '',
      "Email address from which to send all the emails.")
    email_prefix =  Option('svnpolicies', 'email.prefix', '[PROJECT NAME]',
      "Subject prefix for email messages")
    email_attachment =  BoolOption('svnpolicies', 'email.attachment', 'false',
      "Attach diff file with changes")
    email_attachment_limit =  Option('svnpolicies', 'email.attachment_limit', '10000',
      "Maximium attachment size (in bytes)")
    email_subject_cx = BoolOption('svnpolicies', 'email_subject_cx', 'false',
      'Include the context of the commit in the subject.')
    
    log_message_required = BoolOption('svnpolicies', 'log_message.required', 'false',
      "Require log messages on commit")
    log_message_minimum = Option('svnpolicies', 'log_message.minimum', '3',
      "Minimum number of characters required in a log message")
    log_message_pattern = Option('svnpolicies', 'log_message.pattern', '',
      "Regex pattern to match for log message (example: ^ticket #[0-9]+)")

    commands_enabled = BoolOption('svnpolicies', 'commands.enabled', 'false',
      "Enable ticket management control commands in log messages")
    
    advanced_precomit_enabled = BoolOption('svnpolicies', 'advanced_precomit_enabled', 'false',
      "It enables the advanced commands on precommit.")
    
    advanced_postcomit_enabled = BoolOption('svnpolicies', 'advanced_postcomit_enabled', 'false',
      "It enables the advanced commands on postcommit.")
    
    advanced_precomit_file = Option('svnpolicies', 'advanced_precomit_file', '',
      "The path to the advanced commands file that will be processed by the server before svn commit.")
    
    advanced_postcomit_file = Option('svnpolicies', 'advanced_postcomit_file', '',
      "The path to the advanced commands file that will be processed by the server after svn commit.")
    
    svn_property = BoolOption('svnpolicies', 'svn_property', 'false',
      "Enable only authors to update their own checkin comments.")
    
    readonly_repository = BoolOption('svnpolicies', 'readonly_repository', 'false',
      "If enabled then the repository will not permit commits.")
    
    def get_admin_panels(self, req):
        if 'PROJECT_ADMIN' in req.perm:
            yield ('general', _('General'), 'svnpolicies', _('SVN Policies'))

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('PROJECT_ADMIN')
        
        # test if the hooks directory is created(in the trac env) if not create it now
        trac_hooks= self._get_trac_env_path()
        if not os.path.isdir(trac_hooks) :
            os.mkdir(trac_hooks)
        
        # check to see if this is not a help request
        if req.method == 'GET' and req.args.get('help', 0) == '1':
            wiki_help_file_path = api.get_resource_path('svnpolicies/README')
            wiki_help_handler = file(wiki_help_file_path, 'r')
            wiki_help = wiki_help_handler.read()
            wiki_help_handler.close()
            return 'help_svnpolicies.html', { 'wiki_help': wiki_to_html(wiki_help, self.env, req), }
        self.action_status= []
        self.valid_email_flag= True
        self.errors= False
        precomit_advanced_text= ""
        postcomit_advanced_text= ""
        if req.method == 'POST':
            
            # process the boolean options
            self._validate_bool_options(req)
            # process the other options
            for option in ( 'email.list', 'email.prefix', 'email.attachment_limit', 
                           'log_message.minimum', 'log_message.pattern', 
                           'advanced_postcomit_content', 'advanced_precomit_content'):
                if option == 'log_message.pattern' :
                    try :
                        if re.compile(req.args.get(option)) is not None :
                            self.config.set('svnpolicies', option, req.args.get(option))
                        else :
                            self.action_status.append('The log pattern was not saved because is not a valid python regex.')
                            self.log.warning("the " + req.args.get(option) + " is not a valid regex")
                            self.errors= True
                    except:
                        self.action_status.append('The log pattern was not saved because is not a valid python regex.')
                        self.log.warning("the " + req.args.get(option) + " is not a valid regex")
                        self.errors= True
                elif option == 'log_message.minimum' :
                    try :
                        int(req.args.get(option))
                        self.config.set('svnpolicies', option, req.args.get(option))
                    except :
                        self.action_status.append('The log minimum number of characters was not saved because is not a valid python integer.')
                        self.log.warning("the " + req.args.get(option) + " is not a valid number")
                        self.config.set('svnpolicies', option, '')
                        self.config.set('svnpolicies', 'log_message.required', 'false')
                        self.errors= True
                elif not self.valid_email_flag and option == 'email.list' :
                    pass
                elif option == "advanced_postcomit_content":
                    if self.config.getbool('svnpolicies', 'email.enabled') and req.args.get(option) != '' and self.config.getbool('svnpolicies', 'advanced_postcomit_enabled'):
                        # get the trac environmenth
                        trac_env= self._get_trac_env_path()
                        if trac_env != None :
                            # create the file path + file name
                            file_name= trac_env + path.sep + 'advanced-post-commit'
                            #file_path= self._create_advanced_hook('post-commit', req.args.get(option))
                            # save the file_path
                            self.config.set('svnpolicies', "advanced_postcomit_file", file_name)
                            postcomit_advanced_text= req.args.get(option)
                        else :
                            # save the file name 
                            self.config.set('svnpolicies', "advanced_postcomit_file", "")
                    else :
                            # save the file name 
                            self.config.set('svnpolicies', "advanced_postcomit_file", "")
                            self.config.set('svnpolicies', "advanced_postcomit_enabled", "false")
                elif option == "advanced_precomit_content":
                    if self.config.getbool('svnpolicies', 'log_message.required') and req.args.get(option) != '' and self.config.getbool('svnpolicies', 'advanced_precomit_enabled'):
                        # get the trac environment path
                        trac_env= self._get_trac_env_path()
                        if trac_env != None :
                            # create the file path + file name
                            file_name= trac_env + path.sep + 'advanced-pre-commit'
                            #file_path= self._create_advanced_hook('pre-commit', req.args.get(option))
                            # save the file_path
                            self.config.set('svnpolicies', "advanced_precomit_file", file_name)
                            precomit_advanced_text= req.args.get(option)
                        else :
                            self.config.set('svnpolicies', "advanced_precomit_file", "")
                    else :
                            self.config.set('svnpolicies', "advanced_precomit_file", "")
                            self.config.set('svnpolicies', "advanced_precomit_enabled", "false")
                else :
                    self.config.set('svnpolicies', option, req.args.get(option))
            
            if not self.errors :
                
                self._save_settings()
                self._process_new_settings(req)


            
        else :
            # add the content of the advanced files to the textareas 
            try :
                if os.path.isfile(self.config.get('svnpolicies', 'advanced_postcomit_file')) :
                    postcomit_advanced_text= file(self.config.get('svnpolicies', 'advanced_postcomit_file')).readlines();
                if os.path.isfile(self.config.get('svnpolicies', 'advanced_precomit_file')) :
                    precomit_advanced_text= file(self.config.get('svnpolicies', 'advanced_precomit_file')).readlines();
            except Exception, e:
                self.log.error(traceback.format_exc())
        # add the css and js files
        add_script(req, 'svnpolicies/js/tabs.js')
        add_stylesheet(req, 'svnpolicies/css/tabs.css')
        add_script(req, 'svnpolicies/js/svnpolicies.js')
        return 'admin_svnpolicies.html', { 'config':self.config, 'svn_errors': self.errors, 'status': self.action_status, "postcomit_advanced_text": postcomit_advanced_text, "precomit_advanced_text": precomit_advanced_text, }

    def _save_settings(self):
        """
        This method saves the changes settings in the trac ini file.
        """
        config = self.config['svnpolicies']
        registry = Option.registry
        old_registry= {}
        # get them out
        for option, value in config.options() :
            key = 'svnpolicies', option
            old_registry[key]= registry.pop(key)
            
        self.config.save()
        # put them back
        for option, value in config.options() :
            key = 'svnpolicies', option
            registry[key]= old_registry[key]
            
        self.action_status.append('The changes have been saved.')


    def _process_new_settings(self, req):
        """
        This method processes the new settings found in the config
        
        @param req: http request
        
        """
        # create the post commit links
        if self.svnpolicies_enabled and  self.email_enabled :
            if self._do_add_post_commit_hook(req) :
                self.action_status.append('A post commit file was generated')
            else :
                self.action_status.append('The post commit file couldn\'t be generated')
                self.errors= True
        else :
            # delete the hook symlinks because the feature is disabled
            self._delete_hook_links('post-commit')
        # create the pre commit links
        if self.svnpolicies_enabled and self.log_message_required or self.readonly_repository :
            if self._do_add_pre_commit_hook(req) :
                self.action_status.append('A pre commit file was generated')
            else :
                self.action_status.append('The pre commit file couldn\'t be generated')
                self.errors= True
        else :
            # delete the hook symlinks because the feature is disabled
            self._delete_hook_links('pre-commit')
            
        # create the pre commit advanced script
        if self.advanced_precomit_enabled :
            if self.advanced_precomit_file != '' :
                if self._create_advanced_hook(self.advanced_precomit_file, req.args.get("advanced_precomit_content")) :
                    self.action_status.append('The advanced pre commit file was generated.')
                else :
                    self.action_status.append('The advanced pre commit file couldn\'t be generated.')
                    self.errors= True
            else :
                self.action_status.append('The advanced pre commit file couldn\'t be generated.')
                self.errors= True
        
        # create the post commit advanced script
        if self.advanced_postcomit_enabled :
            if self.advanced_postcomit_file != '' :
                if self._create_advanced_hook(self.advanced_postcomit_file, req.args.get("advanced_postcomit_content")) :
                    self.action_status.append('The advanced post commit file was generated.')
                else :
                    self.action_status.append('The advanced post commit file couldn\'t be generated.')
                    self.errors= True
            else :
                self.action_status.append('The advanced post commit file couldn\'t be generated.')
                self.errors= True
        
        # create the pre rev prop commit links
        if self.svn_property:
            if self._do_add_pre_revprop_change_hook(req) :
                self.action_status.append('A pre-revprop-change file was generated')
            else :
                self.action_status.append('The pre-revprop-change file couldn\'t be generated')
                self.errors= True
        else :
            # delete the hook symlinks because the feature is disabled
            self._delete_hook_links('pre-revprop-change')

    def _validate_bool_options(self, req):
        """
        This method processes the boolean options received in a http request by post.
        
        @param req: http request
        """
        for option in  ('readonly_repository',
                        'email.enabled', 'email_from_enabled', 'email.attachment', 'email_subject_cx',
                        'log_message.required', 'commands.enabled', 'svn_property',
                        'svnpolicies_enabled', 'advanced_precomit_enabled', 'advanced_postcomit_enabled'):
            self.log.warning('setting svnpolicies %s=%s'%(option, req.args.get(option,"false")))
            if option == 'email.enabled' :
                if req.args.get('email.enabled',"false") != 'false' :
                    email_list= req.args.get("email.list","false").split(',')
                    if len(email_list) == 0 :
                         self.valid_email_flag= False
                    for email in email_list :
                        if email == '' or not api.validate_email(email) :
                            self.valid_email_flag= False
                            break
                    if self.valid_email_flag :
                        self.config.set('svnpolicies', 'email.enabled', req.args.get('email.enabled',"false"))
                        self.config.set('svnpolicies', 'email.list', req.args.get('email.list',''))
                    else :
                        self.errors= True
                        self.action_status.append('The email list is not valid.')
                        self.log.warning("the email list is not valid.")
                else :
                     self.config.set('svnpolicies', 'email.enabled', "false")
                     self.config.set('svnpolicies', 'email.list', '')
            elif option == 'email_from_enabled' :
                if req.args.get('email.enabled',"false") != 'false' :
                    email= req.args.get("email_from_address","false")
                    email_flag= req.args.get("email_from_enabled", False)
                    
                    if email_flag and self.config.getbool('svnpolicies', 'email.enabled'):
                        if email != '' and api.validate_email(email) :
                            self.config.set('svnpolicies', option, req.args.get(option,"false"))
                            self.config.set('svnpolicies', 'email_from_address', email)
                        else :
                            self.errors= True
                            self.action_status.append('The from email address is not valid.')
                            self.log.warning("the from email address is not valid.")
                    else :
                        self.config.set('svnpolicies', 'email_from_enabled', 'false')
                        self.config.set('svnpolicies', 'email_from_address', '')
                    
            elif  option == 'advanced_postcomit_enabled' :
                if not self.config.getbool('svnpolicies', 'email.enabled') or req.args.get(option,"false") == "false":
                    # delete the hook file
                    self._delete_file(self.config.get('svnpolicies', 'advanced_postcomit_file'))
                    # delete the config file value
                    self.config.set('svnpolicies', "advanced_postcomit_file", "")
                    # set to false the value
                    self.config.set('svnpolicies', option, 'false')
                else :
                    self.config.set('svnpolicies', option, req.args.get(option,"false"))
                    self.config.set('svnpolicies', 'advanced_postcomit_file', "")

            elif option == 'advanced_precomit_enabled':
                if not self.config.getbool('svnpolicies', 'log_message.required') or req.args.get(option,"false") == "false":
                    # delete the hook file
                    self._delete_file(self.config.get('svnpolicies', 'advanced_precomit_file'))
                    # delete the config file value
                    self.config.set('svnpolicies', "advanced_precomit_file", "")
                    # set to false the value
                    self.config.set('svnpolicies', option, 'false')
                else :
                    self.config.set('svnpolicies', option, req.args.get(option,"false"))
                    self.config.set('svnpolicies', 'advanced_precomit_file', "")
            else :
                self.config.set('svnpolicies', option, req.args.get(option,"false"))


    def _create_advanced_hook(self, file_name, file_content):
        """
        This method creates a file in the trac hook directory.
        
        @param file_name: String
        @param file_content: String
        @return: boolean
        """
        # clean file content from windows cr character
        file_content= file_content.replace('\r', '')
        try :
            # if the file exists ... delete it
            self._delete_file(file_name)
            # create the file
            file_handle= file(file_name, "w")
            # write the content
            file_handle.write(file_content)
            # close the file
            file_handle.close()
            # make it executable
            os.chmod(file_name, stat.S_IRWXU)
        except Exception, e:
            self.log.error(traceback.format_exc())
            return False
        return True
    
    def _delete_file(self, file_name):
        """
        This method deletes a file from the system
        
        @param file_name: String
        @return: boolean
        """
        try :
            if os.path.isfile(file_name) :
                os.unlink(file_name)
                self.log.warning("delete the advanced hook file" + file_name)
                return True
        except Exception, e:
            self.log.error(traceback.format_exc())
            return False
        return False

    def _do_add_pre_revprop_change_hook(self, req):
        """
        This method adds a file in the hooks directory of the svn repository, 
        hook that acts on change on a property of the repository.
        
        @param req: http request object
        @return: boolean
        """
        if not self.config.getbool('svnpolicies', 'svnpolicies_enabled') and  not self.config.getbool('svnpolicies', 'svn_property'):
            return False

        # get the svn path
        svn_repository= self._get_svn_hook_path()
        if svn_repository == None :
            return False
        
        # get the trac environment path
        trac_env= self._get_trac_env_path()
        if trac_env == None :
            return False
        # delete the old hook symlinks
        self._delete_hook_links('pre-revprop-change')
        return self._create_hook_links('pre-revprop-change', svn_repository, trac_env)
   
    def _do_add_pre_commit_hook(self, req):
        """
        This method adds a file in the hooks directory of the svn repository, 
        hook that acts before a commit is made on the repository.
        
        @param req: http request object
        @return: boolean
        """
        if not self.config.getbool('svnpolicies', 'svnpolicies_enabled') and  not self.config.getbool('svnpolicies', 'log_message.required'):
            return False

        # get the svn path
        svn_repository= self._get_svn_hook_path()
        if svn_repository == None :
            return False
        
        # get the trac environment path
        trac_env= self._get_trac_env_path()
        if trac_env == None :
            return False
        # delete the old hook symlinks
        self._delete_hook_links('pre-commit')
        return self._create_hook_links('pre-commit', svn_repository, trac_env)
    
    def _do_add_post_commit_hook(self, req):
        """
        This method adds a file in the hooks directory of the svn repository, 
        hook that acts after a commit is made on the repository.
        
        @param req: http request object
        @return: boolean
        """
        if not self.config.getbool('svnpolicies', 'svnpolicies_enabled') and  not self.config.getbool('svnpolicies', 'email.enabled'):
            return False

        # get the svn path
        svn_repository= self._get_svn_hook_path()
        if svn_repository == None :
            return False
        
        # get the trac environment path
        trac_env= self._get_trac_env_path()
        if trac_env == None :
            return False
        # delete the old hook symlinks
        self._delete_hook_links('post-commit')
        
        return self._create_hook_links('post-commit', svn_repository, trac_env)
    
    def _get_svn_hook_path(self):
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
                    return str(repository) + os.path.sep +'hooks'
        except Exception, e:
            self.log.error(traceback.format_exc())
            self.log.error(e)
            return None
        
    def _get_trac_env_path(self):
        """
        This method returns the path on the system where the
        svn server expects the hook file to be present. The trac 
        configuration file provides the svn repository information.
        
        @return: String
        If a error ocurs in the process of getting the path the method 
        returns None.
        """
        try :
            env= self.env.path
            return str(env) + os.path.sep +'hooks'
        except Exception:
            return None
    
    def _delete_hook_links(self, link_name):
        """
        This method removes the symbolic links made on the system in order
        for the svn "link_name" hook not to be triggered on commits. 
        
        @return: boolean
        @param link_name: String 
        """
        
        # get the svn path
        svn_repository= self._get_svn_hook_path()
        svn_hook= svn_repository + os.path.sep + link_name
        if svn_repository == None :
            return False
        
        # get the trac environment path
        trac_env= self._get_trac_env_path()
        trac_hook= trac_env + os.path.sep + link_name
        if trac_env == None :
            return False
        
        try :
            # test the parameters
            if not os.path.isdir(svn_repository) or not os.path.isdir(trac_env) :
                self.log.warning("the parameteres are not directories")
                raise Exception()
            
            # add link from the generic post-commit file to a file in the project trac environment

            if os.path.islink(trac_hook) :
                self.log.warning("deleted the file: " + trac_hook)
                os.unlink(trac_hook)
            # add link from the trac environment to the svn repository
            if os.path.islink(svn_hook) :
                self.log.warning("deleted the file: " + svn_hook)
                os.unlink(svn_hook)
        except Exception, e:
            self.log.error(traceback.format_exc())
            self.log.error(e)
            return False
        return True
    
    def _extract_the_hook_script(self, resource_name):
        """
        This method extracts the required hook file from the zipped egg
        and returnes the path to the unzipped file.
        
        @param resource_name: String
        @return: String
        """
        return api.get_hook_path(resource_name)
    
    def _create_hook_links(self, link_name, svn_path, trac_env_path):
        """
        This method is used to create a symbolic links on the system. The method
        tries to create two symbolic links, one in the trac environment hooks directory
        and one in the svn repository hooks directory. The first link points to a generic
        script in the trac plugin and the second points to the first link. This mesh of 
        link is created to be able, at runtime, to determine the trac.ini file.
        
        @param link_name: String
        @param svn_path: String
        @param trac_env_path: String
        @return: boolean
        """
        try :
            # test the parameters
            if not os.path.isdir(svn_path) or not os.path.isdir(trac_env_path) :
                self.log.warning("the parameteres are not directories")
                self.log.warning(svn_path)
                self.log.warning(trac_env_path)
                raise Exception() 
            # create the path to the generic hook file
            generic_script= self._extract_the_hook_script(link_name + ".py")
            
            if not os.path.isfile(generic_script) :
                self.log.warning("the generic script " + generic_script + " isn't on the computed path")
                raise Exception()
            # add link from the generic post-commit file to a file in the project trac environment
            os.symlink(generic_script, trac_env_path + os.path.sep + link_name)
            self.log.warning("created link " + trac_env_path + os.path.sep + link_name + " to the generic script")
            # add link from the trac environment to the svn repository
            os.symlink(trac_env_path + os.path.sep + link_name, svn_path + os.path.sep + link_name)
            self.log.warning("created link " + svn_path + os.path.sep + link_name + " to the trac environment link")
        except Exception, e:
            self.log.error(traceback.format_exc())
            self.log.error(e)
            return False
        return True
    
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('svnpolicies', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
