#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
'''
YumlPreprocessor.py

Includes a UML diagram as an image using the http://yuml.me API.
'''

from trac.wiki.macros import WikiMacroBase
import re
import urllib

revison = "$Rev$"
url = "$URL$"

pragmaRE = re.compile('^# pragma (.*) #$', re.MULTILINE)

def yuml_url(prefix, content):
    pragmaMatch = pragmaRE.search(content)
    if pragmaMatch:
        pragma = urllib.quote(pragmaMatch.group(1),';:')
    else:
        pragma = 'scruffy'
    content = content.strip().replace('\n', ', ')
    return '<img src="http://yuml.me/diagram/' + pragma + '/' + prefix + '/' + urllib.quote(content) + '" />'

class YumlUseCaseMacro(WikiMacroBase):
    '''
    Includes a UML diagram as an image using the yuml.me API.
    This is intended to be used as a preprocessor.
    '''

    revision = "$Rev$"
    url = "$URL$"

    def expand_macro(self, formatter, name, content):
        '''
        Use this macro as a preprocessor macro. The content is a valid
        UseCase notation as per yuml.me. You may insert newlines.
        
        Example usage: (from website)
        {{{
        #!YumlUseCase
        [User]-(Login)
        [User]-(Logout) 
        (Login)<(Reminder) 
        (Login)>(Captcha)
        }}}
        '''
        return yuml_url('usecase', content)

class YumlClassMacro(WikiMacroBase):
    '''
    Includes a UML diagram as an image using the yuml.me API.
    This is intended to be used as a preprocessor.
    '''

    revision = "$Rev$"
    url = "$URL$"

    def expand_macro(self, formatter, name, content):
        '''
        Use this macro as a preprocessor macro. The content is a valid
        class diagram notation as per yuml.me. You may insert newlines.
        
        Example usage: (from website)
        {{{
        #!YumlClass
        [Customer]+1->*[Order]
        [Order]++1-items >*[LineItem]
        [Order]-0..1>[PaymentMethod]
        }}}
        '''
        return yuml_url('class', content)

class YumlActivityMacro(WikiMacroBase):
    '''
    Includes a UML diagram as an image using the yuml.me API.
    This is intended to be used as a preprocessor.
    '''

    revision = "$Rev$"
    url = "$URL$"

    def expand_macro(self, formatter, name, content):
        '''
        Use this macro as a preprocessor macro. The content is a valid
        activity diagram notation as per yuml.me. You may insert newlines.
        
        Example usage: (from website)
        {{{
        #!YumlActivity
        (start)-><d1>logged in->(Show Dashboard)->|a|->(end)
        <d1>not logged in->(Show Login)->|a|
        }}}
        '''
        return yuml_url('activity', content)
