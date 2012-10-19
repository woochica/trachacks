# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Takanori Suzuki <takanorig@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from os import environ

class LocaleUtil:
    
    def get_locale(self, req):
        """Get client locale from the http request."""
        
        locale = None
        locale_array = None
        
        if req.environ.has_key('HTTP_ACCEPT_LANGUAGE'):
            locale_array = req.environ['HTTP_ACCEPT_LANGUAGE'].split(",")
        
        if locale_array and (len(locale_array) > 0):
            locale = locale_array[0].strip()
        
        if locale and (len(locale) > 2):
            locale = locale[0:2];
        
        return locale
