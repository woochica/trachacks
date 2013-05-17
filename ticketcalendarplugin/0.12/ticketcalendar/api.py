# -*- coding: utf_8 -*-
#
# Copyright (C) 2013 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.config import Option, ListOption, IntOption
from trac.util import arity
from trac.util.translation import domain_functions, dgettext


TEXTDOMAIN = 'ticketcalendar'


_, tag_, N_, gettext, add_domain = domain_functions(
    TEXTDOMAIN,
    ('_', 'tag_', 'N_', 'gettext', 'add_domain'))


if arity(Option.__init__) <= 5:
    def _option_with_tx(Base): # Trac 0.12.x
        class Option(Base):
            def __getattribute__(self, name):
                val = Base.__getattribute__(self, name)
                if name == '__doc__':
                    val = dgettext(TEXTDOMAIN, val)
                return val
        return Option
else:
    def _option_with_tx(Base): # Trac 1.0 or later
        class Option(Base):
            def __init__(self, *args, **kwargs):
                kwargs['doc_domain'] = TEXTDOMAIN
                Base.__init__(self, *args, **kwargs)
        return Option


Option = _option_with_tx(Option)
IntOption = _option_with_tx(IntOption)
ListOption = _option_with_tx(ListOption)
