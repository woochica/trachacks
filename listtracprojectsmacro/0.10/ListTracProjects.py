# Current version Author:
#   Mark Thomas <mathomas@aero.org>
#
# Based on code from http://trac.edgewall.org/wiki/MacroBazaar#ListTracProjects
# by:
#  robert@exa-omicron.nl  
#
# Portions of this code were copied from
# trac.web.main.py
# Authors: 
#  Christopher Lenz <cmlenz@gmx.de>
#  Matthew Good <trac@matt-good.net>


"""
	List All Trac Projects in a scalable format.
	
	Administrators _must_ set the ENV_PARENT_DIR variable
	in order for the macro to work properly. 

	Sample call:
	[[ListTracProjects()]]
"""

import os
import dircache
import string
from trac.env import open_environment
from trac.web.href import Href
from trac.util.text import to_unicode

def execute(hdf, txt, env):
	### ATTENTION!! SET THIS VARIBALE
	ENV_PARENT_DIR = '/usr/local/www/trac'
	##

	# Create the index
	# The index will only display links to the first letters
	# of existing projects. e.g. if Apple, Charlie,
	# and Zoo are the only projects under ENV_PARENT_DIR,
	# the index will display "A : C : Z" for the index
	str = '<div id="index">'

	proj_groups = get_projects(ENV_PARENT_DIR)
	sorted_keys = proj_groups.keys()
	sorted_keys.sort()

	for ltr in sorted_keys:
		# This has to be done first so that it is at the top of the page
		# optional: output number of projects in each category
		# output sorted html index 
		str += '<a href="#' + string.upper(ltr) + '">' + string.upper(ltr) + '</a> : '
	str = str[:-3]		# remove unsightly trailing colon
	str += '</div>'
	
	# Create alphabetized tables of projects
	for grp in sorted_keys:
		# Output link back to index
		bigLtr = string.upper(grp)
		str += '<a href="#index"><h2 id="' + bigLtr + '">' \
			+ bigLtr + '</h2></a>'
		# Output number of projects
		str += '<table class="wiki">'
		proj_groups[bigLtr].sort(lambda x, y: cmp(x['name'].lower(), y['name'].lower()))
		for p in proj_groups[bigLtr]:
			str += '<tr><td><a href="' + p['href'] + \
				'" target="_new">' + p['name'] + \
				'</a></td><td>' + p['description'] + '</td></tr>'
		str += '</table>'

	return str

# The code below is based on portions from trac.web.main.py
# Authors:
#  Christopher Lenz <cmlenz@gmx.de>
#  Matthew Good <trac@matt-good.net>
#       
# It has been slightly modified by the current author
# mostly to remove dependencies on the web frontend.
def get_projects(ENV_PARENT_DIR):
	href = Href('')
	project_groups = {}
	#projects = []
	for env_name, env_path in get_environments(ENV_PARENT_DIR).items():
	    try:
		#env = _open_environment(env_path,
		#                        run_once=environ['wsgi.run_once'])
		env = open_environment(env_path)
		proj = {
		'name': env.project_name,
		'description': env.project_description,
		'href': href(env_name)
		#'href': env_name
		}
	    except Exception, e:
		proj = {'name': env_name, 'description': to_unicode(e)}
	    # Add to the specified group based on first letter
	    # ToDo: Does this work for numbers and symbols?
	    if project_groups.has_key(string.upper(proj['name'][0])):
		project_groups[string.upper(proj['name'][0])].append(proj)
	    else:
		# Initialize the new list
		project_groups[string.upper(proj['name'][0])] = [proj]
	return project_groups

def get_environments(ENV_PARENT_DIR, warn=False):
    """Retrieve canonical environment name to path mapping.

    The environments may not be all valid environments, but they are good
    candidates.
    """

    env_paths = []	# Initialize variable

    if ENV_PARENT_DIR:
        ENV_PARENT_DIR = os.path.normpath(ENV_PARENT_DIR)
        paths = dircache.listdir(ENV_PARENT_DIR)[:]
        dircache.annotate(ENV_PARENT_DIR, paths)
        env_paths += [os.path.join(ENV_PARENT_DIR, project) \
                      for project in paths if project[-1] == '/']
    envs = {}
    for env_path in env_paths:
        env_path = os.path.normpath(env_path)
        if not os.path.isdir(env_path):
            continue
        env_name = os.path.split(env_path)[1]
        if env_name in envs:
            if warn:
                print >> sys.stderr, ('Warning: Ignoring project "%s" since '
                                      'it conflicts with project "%s"'
                                      % (env_path, envs[env_name]))
        else:
            envs[env_name] = env_path
    return envs
