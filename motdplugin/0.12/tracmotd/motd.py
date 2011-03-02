#
# Created by Christian Masopust 2011
# Copyright (c) 2011 Christian Masopust. All rights reserved.
#

import re
import time
import datetime
import os.path

from trac.core 		import Component, implements
from trac.web.api	import IRequestFilter
from trac.web.chrome	import ITemplateProvider, add_stylesheet, add_script, add_script_data
from trac.config	import Option, Configuration

__all__ = ['MessageOfTheDayPlugin']

class MessageOfTheDayPlugin(Component):
    """ Provides a plugin to insert a 'Message Of The Day' to each page.
        This plugin is limited to the features of the methods
        add_link, add_stylesheet and add_script from trac.web.chrome,
        so not all valid (X)HTML attributes can be set.
    """
    implements(ITemplateProvider, IRequestFilter)

    section = 'motd'
    message_dir = Option(section, 'message_dir', '/data/motd.d', 'Directory for motd-files.')
    message_file = Option('motd', 'message_file', '/data/message.ini', 'Ini-file style motd-file.')


    # ITemplateProvider methods:
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
	return [('tracmotd', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []


    # IRequestFilter methods:
    #
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        config = Configuration(self.message_file)

	d = self._read_messages(req, config)
	#self.log.debug('post_process_request: dictionary-len: ' + str(len(d)))
	if (len(d) > 0):
	    add_script_data(req, d)
	    add_script(req, 'tracmotd/date.js')
	    add_script(req, 'tracmotd/motd.js')
	    add_stylesheet(req, 'tracmotd/motd.css')

        return (template, data, content_type)


    # private methods:
    #
    def _read_messages(self, req, config):

	current_datetime = datetime.datetime.now()
	d = {}

        sections = config.sections(defaults=False)
	for section in sections:
	    if req.incookie.has_key(section):
	        cookie_val = req.incookie[section]
		#self.log.debug('_read_messages: cookie_val = ' + cookie_val.value)
		if cookie_val.value == "shown":
		    continue

	    title = config.get(section, 'title', default='')
	    message = config.get(section, 'message', default='nomessage')
	    priority = config.getint(section, 'priority', default=0)
	    valid_until = config.get(section, 'valid_until', default='forever')
	    repeat = config.get(section, 'repeat', default='no')

	    valid_until_date = datetime.datetime(*time.strptime(valid_until, "%Y-%m-%d %H:%M")[0:5])
	    if (valid_until_date > current_datetime):
		if message == 'nomessage':
		    # get message from file
		    message = self._read_message_from_file(section)

	        d[section] = { 'title': title,
                               'message': message,
                               'priority': priority,
                               'valid_until': valid_until
	                     }

	if (len(d) > 0):
            return { 'TracMotd': d }
	else:
            return {}


    def _read_message_from_file(self, section):
        # get message from file named "section.html"
	message_file = section + '.html'
	message_file = os.path.join(self.message_dir, message_file)
	with open(message_file, 'r') as mf:
	    return mf.read()
        

