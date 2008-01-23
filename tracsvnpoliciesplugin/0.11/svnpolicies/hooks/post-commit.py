#!/usr/bin/env python
from loader import *


from commands import mkarg # nifty routine to add shell quoting
import os
import sys
import subprocess 


def epopen(cmd):
    """
    This function adds some variables in the environment before
    running a command.
    
    @param cmd: String
    @return: (subprocess_stdin_handle, subprocess_stdout_stderr_handle)
    """
    global production, PYTHONPATH
    # env is a dictionary of environment variables    
    prefix= ""
    if PYTHONPATH != "" and production:
        prefix= "export \"PYTHONPATH=%s\"; \n" % PYTHONPATH
    print prefix
    p = subprocess.Popen(prefix + cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out_text= p.stdout.readlines()
    pid, status = os.waitpid(p.pid, 0)
    status = status%255
    return status, out_text

def run_command(command):
    """
    This function tries to run a command on to the sistem
    and returnes a tuple composed from the exit status and 
    the output of the command.
    
    @param command: list
    @return: (int, String)
    """
    status= 0
    response= ''
    try :
        status, response_list = epopen(' '.join(command))
        if len(response_list) > 0 : 
            response= '\n'.join(response_list)
        else :
            response= ""
    except Exception, e:
        status= 4
        response= "Error in invoking the command "
        import traceback
        response += traceback.format_exc()
    return (status, response)

def build_command(repos, rev, settings, project_name):
    """
    This function tries to build a list with the command 
    used for sending emails regarding svn commits.
    
    @param repos: String
    @param rev: int
    @param settings: dict
    @param api_hook: svnpolicies.api.IniReader
    """
    global SVNLOOK, SVNNOTIFY, CHANGESET_URL, AUTHOR_URL_TEMPLATE, CREDENTIALS
    if settings['TO_LIST'] == '' :
        return None
    to_list= settings['TO_LIST']
    command= [SVNNOTIFY, "--repos-path", repos,
            "--revision", str(rev),
            "--to", "\"" + to_list + "\"",
            "--svnlook", SVNLOOK,
            "--handler HTML::ColorDiff --user-domain optaros.com", ]
    
    if settings['MAIL_FROM'] and settings['MAIL_FROM_ADDRESS'] != '':
        command.extend(['--from', settings['MAIL_FROM_ADDRESS'],])
    
    # set the subject-cx flag
    if settings['MAIL_SUBJECT_CX'] :
        command.append('--subject-cx')
    # we attach the diff or include it in the email
    if settings['MAIL_ATTACH'] :
        # attach
        command.append("-a")
    else :
        # include
        command.append("-d")
    if settings['MAIL_ATTACH_SIZE'] :
        command.extend(["-e", settings['MAIL_ATTACH_SIZE'],])

    command.extend(["-P", "\"" + settings['MAIL_SUBJECT'] + "\"",
            CREDENTIALS,
            "--author-url", AUTHOR_URL_TEMPLATE,
            "-U", CHANGESET_URL % (project_name, '%s')])
    return command


def run_trac_advanced(settings, repos, rev):
    """
    This method tries to run the script edited by the project admin.
    
    @param settings: dict
    @param repos: String
    @param rev: int
    @return: (int, String)
    """
    if not settings['ADVANCED_POST'] :
        return 0,''
    return run_command([settings['ADVANCED_POST_FILE'], 
                                   str(repos),
                                   str(rev),])
    

def run_trac_commands(settings, rev, trac_env):
    """
    This method tries to run the script that executs commands from log messages.
    
    @param settings: dict
    @param repos: String
    @param rev: int
    @return: (int, String)
    """
    global TRAC_CODE_PATH
    if not settings['COMMANDS'] :
        return 0,''
    return run_command([TRAC_CODE_PATH + os.path.sep +'contrib' + os.path.sep + 'trac-post-commit-hook', 
                                   '-r',
                                   str(rev),
                                   '-p',
                                   str(trac_env),])


if __name__ == "__main__":
    
    
    #######################################
    # STEP 1 - Read and parse the ARGUMETS
    #######################################
    arguments= sys.argv[1:]
    # process the parameters
    if len(arguments) != 2 :
        sys.stderr.write("wrong number of arguments!")
        sys.exit(1)
        
    repos= arguments[0]
    if not os.path.isdir(repos) :
        sys.stderr.write("the svn repository isn't set properly")
        sys.exit(2)
    try :
        rev= int(arguments[1])
    except ValueError:
        sys.stderr.write("bad revision number")
        sys.exit(3)
        
    #############################################
    # STEP 2 - Get the Trac ini SETTINGS
    #############################################
    # read the ini file of the trac enviroment
    config= api.IniReader(get_trac_path(__file__))
    status= 0
    response= ''
    #############################################
    # STEP 3 - Try to send the commit email
    #############################################    
    # make the command
    command= build_command(repos, rev, config.get_svn_policy_settings(), config.get_project_name())
    if command != None :
        # run it
        status, response= run_command(command)

    ################################################
    # STEP 4 - Try to run the Trac COMMANDS script
    ################################################
    command_status, command_response= run_trac_commands(config.get_svn_policy_settings(), rev, config.get_project_path())
    if response != '' :
        response += '\n' 
    response += command_response 
    status= status or command_status

    #################################################################
    # STEP 5 - Try to run the scripts from the trac hooks directory
    #################################################################
    advanced_status, advanced_response= run_trac_advanced(config.get_svn_policy_settings(), repos, rev)
    if response != '' :
        response += '\n' 
    response += advanced_response 
    status= status or advanced_status
    
    ################################################################
    # STEP 6 - Exit the Hook 
    ################################################################
    if response != '':
        sys.stderr.write(response)
    sys.exit(status)
    
