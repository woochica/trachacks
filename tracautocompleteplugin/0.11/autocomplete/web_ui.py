# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         web_ui.py
# Purpose:      The auto complete file handler module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------
from trac.core import *
from trac.web.chrome import *
from trac.util.html import html

from trac.web import IRequestHandler
from trac.web.api import RequestDone, HTTPException
from trac.web.api import ITemplateStreamFilter

from pkg_resources import resource_filename

import sys, os
import time
import re

__all__ = ['AutoComplete']

class AutoComplete(Component):
    implements(ITemplateProvider,
               IRequestHandler, 
               ITemplateStreamFilter,
               )

    # hours of cache aging
    UserCacheAge = 24

    # {email:(zh_name, description), }
    QueryUserCache = {}
    # {queyr: time, }
    QueryUserHistory = {}

    # ITemplateProvider
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('autocomplete', resource_filename(__name__, 'htdocs'))]

    # IRequestHandler

    def match_request(self, req):
        return req.path_info.startswith("/ac_query")

    def process_request(self, req):
        if req.path_info.startswith("/ac_query/user"):
            # get query string
            query = req.args.get('q')
            limit = int(req.args.get('limit', 1500))

            # query
            message = self._handle_query_user(query, limit)
            # return result
            self._send_response(req, message)

    # ITemplateStreamFilter
    
    def filter_stream(self, req, method, filename, stream, data):
        if req.path_info.startswith("/newticket") or req.path_info.startswith("/ticket"):

            css_files = [
                        "jquery-ui/ui.all.css",
                        "jquery.autocomplete.css",
                        ]
            js_files = [
                        "jquery-ui/ui.core.js",
                        "jquery-ui/ui.draggable.js",
                        "jquery-ui/ui.resizable.js",
                        "jquery-ui/ui.dialog.js",
                        "jquery-ui/jquery.bgiframe.js",
                        "jquery.autocomplete.js",
                        "autocomplete.js",
                        ]

            # common css files
            for css_file in css_files:
                add_stylesheet(req, 'autocomplete/' + css_file)

            # common js files
            for js_file in js_files:
                add_script(req, 'autocomplete/' + js_file)
                
        return stream

    # internal methods

    def _handle_query_user(self, query, limit):
        """
        """
        # query
        result = self._query_user(query, limit)

        # convert to string
        message = "\n".join(result).encode('utf-8')
        
        return message

    def _query_user(self, query, limit):
        """
        """
        now = int(time.time())
        history_time = self.QueryUserHistory.get(query, 0)
        if now - history_time > 60 * 60 * self.UserCacheAge:
            # update cache
            self._update_user_cache(query)
            # update history
            self.QueryUserHistory[query] = now

        # query cache
        result = self._query_user_cache(query)
        if result:
            result = result[:limit]
        return result

    def _update_user_cache(self, query):
        """
        """
        # query
        rows = self._email_complete(query)
        # update cache
        for row in rows:
            email = row.get("email").lower()
            zh_name = row.get("zh_name")
            description = row.get("description", "")
            self.QueryUserCache[email] = (zh_name, description)

    def _query_user_cache(self, query):
        """
        """
        result = []
        for email, zh_name_description in self.QueryUserCache.items():
            zh_name, description = zh_name_description
            if email.startswith(query):
                record = email + u'|' + zh_name + u'-' + description
                result.append(record)
        result.sort()
        return result

    def _email_complete(self, email_init_str):
        """
        return:
        [{'email': {'email': 'user@example.com', 'zh_name': u'user name'}]
        """
        email_init_str = email_init_str.lower().strip()
        try:
            email_init_str.decode('ascii')
        except (UnicodeDecodeError , UnicodeEncodeError):
            return []
        
        if len(email_init_str) < 2:
            return None
            
        return_list = []
        f = open("conf/username_list.txt", "r")
        for line in f.readlines():
            m = re.match("(.*)\[(.*)\]", line.decode("utf-8"))
            if m:
                email, zh_name = m.group(1), m.group(2)
                email = email.lower().strip()
                if email.startswith(email_init_str):
                    return_list.append({"email": email, "zh_name": zh_name})
        return return_list
        
    def _send_response(self, req, message):
        """
        """
        req.send_response(200)
        req.send_header('Cache-control', 'no-cache')
        req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        req.send_header('Content-Type', 'text/plain')
        req.send_header('Content-Length', len(isinstance(message, unicode) and message.encode("utf-8") or message))
        req.end_headers()

        if req.method != 'HEAD':
            req.write(message)
        raise RequestDone

