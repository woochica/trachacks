# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>
# 
# Concept code for template filter created by Noah Kantrowitz on
# 2008-02-19.

import re
import copy

from genshi.filters.transform import Transformer
from genshi.builder import tag, TEXT

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider
from trac.mimeview.api import Context
from trac.web.chrome import add_ctxtnav, add_link, add_script, add_stylesheet, \
                            add_warning, INavigationContributor, Chrome
from trac.config import Option, ListOption
from trac.util import get_reporter_id

from dateutil.parser import parse

__all__ = ['DateDueHandler']

# The thought here being to have the plugin verify that the date_due
# ticket custom filed is configured.

#class FieldSetupModule(Component):
#    """ Handles the verification and setup of ticket-custom fields """
#    implements (IEnvironmentSetupParticipant)


class DateDueHandler(Component):
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        """ Hack up the query inteface to do what we want. """
        print("filtering stream: %s" % filename)
        if filename in ['ticket.html']:
            stream |= Transformer('.//td[@headers="h_due_date"]/text()'
                                 ).map(self._convert_date, TEXT)
        elif filename in ['tasklist.html', 'query.html']:
            stream |= Transformer('.//td[@class="due_date"]/text()'
                                 ).map(self._convert_date, TEXT)
        return stream

    def _convert_date(self, m):
        data = str(m.strip())
        if not data:
            return m
        if data == '--':
            return data
        date = parse(data)
        return date.strftime('%m/%d/%Y')
        
    
