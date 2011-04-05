"""
 Created by Christian Masopust 2011
 Copyright (c) 2011 Christian Masopust. All rights reserved.
"""

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
    """
    implements(ITemplateProvider, IRequestFilter)

    section = 'motd'
    message_dir  = Option(section, 'message_dir',  '/data/motd.d',      'Directory for motd-files')
    message_file = Option(section, 'message_file', '/data/message.ini', 'Ini-file style motd-file')
    date_format  = Option(section, 'date_format',  '%Y-%m-%d %H:%M',    'Date format for expiration date')
    frame_width  = Option(section, 'frame_width',  '500',               'Frame width in px')
    frame_height = Option(section, 'frame_height', '400',               'Frame height in px')


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

        frame_width = self.frame_width
        if frame_width == '': frame_width = '500'
        frame_height = self.frame_height
        if frame_height == '': frame_height = '400'

	d = self._read_messages(req, config)
	#self.log.debug('post_process_request: dictionary-len: ' + str(len(d)))
	if (len(d) > 0):
            frame_data = {'TracMotdFrame': {'frame_width': frame_width, 'frame_height': frame_height} }
	    add_script_data(req, frame_data)
	    add_script_data(req, d)
	    add_script(req, 'tracmotd/js/date.js')
	    add_script(req, 'tracmotd/js/motd.js')
	    add_stylesheet(req, 'tracmotd/css/motd.css')

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

		cArr = cookie_val.value.split('-')
		if len(cArr) != 4:
		    # cookie invalid, ignore message (TODO: think about :-)
		    continue

		deltas = {"m": 60, "h": 3600, "d": 86400, "w": 604800 }
		lastShown = int(cArr[3]) / 1000
		now = int(time.time())
		#self.log.debug('_read_messages: lastShown=' + str(lastShown))
		#self.log.debug('_read_messages: now      =' + str(now))
		delta = deltas[cArr[2].lower()]
		if lastShown + delta > now:
		    # don't show message now
		    continue

	    title = config.get(section, 'title', default='')
	    message = config.get(section, 'message', default='nomessage')
	    priority = config.getint(section, 'priority', default=0)
	    valid_until = config.get(section, 'valid_until', default='forever')
	    repeat = config.get(section, 'repeat', default='no')

	    # check repeat-syntax
	    rArr = repeat.split('-')
	    if len(rArr) != 2: repeat = 'no'
	    else:
	        if rArr[0].isdigit():
		    if int(rArr[0]) < 1: repeat = 'no'
		else: repeat = 'no'

		intervalValues = [ 'm', 'M', 'h', 'H', 'd', 'D', 'w', 'W' ]
		if not rArr[1] in intervalValues: repeat = 'no'
		    
	    #self.log.debug('_read_messages: date_format = ' + self.date_format)
	    valid_until_date = datetime.datetime(*time.strptime(valid_until, self.date_format)[0:5])
	    if (valid_until_date > current_datetime):
		if message == 'nomessage':
		    # get message from file
		    message = self._read_message_from_file(section)
		    if message == '':
		        # no message, continue...
			continue

	        d[section] = { 'title': title,
                               'message': message,
                               'priority': priority,
                               'valid_until': valid_until,
			       'repeat': repeat
	                     }

	if (len(d) > 0):
            return { 'TracMotd': d }
	else:
            return {}


    def _read_message_from_file(self, section):
        # get message from file named "section.html"
	message_file = section + '.html'
	message_file = os.path.join(self.message_dir, message_file)
	if os.path.exists(message_file):
	    try:
	        mf = open(message_file, 'r')
	        mess = ''
	        try:
	            mess = mf.read()
	        finally:
	            mf.close()
	        return mess
	    except IOError:
	        return ''
	else:
	    return ''
        

