'''
YumlPreprocessor.py

Includes a UML diagram as an image using the http://yuml.me API.
'''

from trac.wiki.macros import WikiMacroBase

revison = "$Rev$"
url = "$URL$"

class YumlUseCaseMacro(WikiMacroBase):
    '''
    Includes a UML diagram as an image using the http://yuml.me API.
    This is intended to be used as a preprocessor.
    '''

    revision = "$Rev$"
    url = "$URL$"

    def expand_macro(self, formatter, name, content):
        '''
        Use this macro as a preprocessor macro. The content is a valid
        UseCase notation as per http://yuml.me. You may insert newlines.
        
        Example usage: (from website)
        {{{
        #!YumlUseCase
        [User]-(Login)
        [User]-(Logout) 
        (Login)<(Reminder) 
        (Login)>(Captcha)
        }}}
        '''
        content = content.strip().replace('\n', ', ')
        return '<img src="http://yuml.me/diagram/scruffy/usecase/' + content + '" />'
    
    # Note that there's no need to HTML escape the returned data,
    # as the template engine (Genshi) will do it for us.

class YumlClassMacro(WikiMacroBase):
    '''
    Includes a UML diagram as an image using the http://yuml.me API.
    This is intended to be used as a preprocessor.
    '''

    revision = "$Rev$"
    url = "$URL$"

    def expand_macro(self, formatter, name, content):
        '''
        Use this macro as a preprocessor macro. The content is a valid
        class diagram notation as per http://yuml.me. You may insert newlines.
        
        Example usage: (from website)
        {{{
        #!YumlClass
        [Customer]+1->*[Order]
        [Order]++1-items >*[LineItem]
        [Order]-0..1>[PaymentMethod]
        }}}
        '''
        content = content.strip().replace('\n', ', ')
        return '<img src="http://yuml.me/diagram/scruffy/class/' + content + '" />'
    
    # Note that there's no need to HTML escape the returned data,
    # as the template engine (Genshi) will do it for us.

class YumlActivityMacro(WikiMacroBase):
    '''
    Includes a UML diagram as an image using the http://yuml.me API.
    This is intended to be used as a preprocessor.
    '''

    revision = "$Rev$"
    url = "$URL$"

    def expand_macro(self, formatter, name, content):
        '''
        Use this macro as a preprocessor macro. The content is a valid
        activity diagram notation as per http://yuml.me. You may insert newlines.
        
        Example usage: (from website)
        {{{
        #!YumlActivity
        (start)-><d1>logged in->(Show Dashboard)->|a|->(end)
        <d1>not logged in->(Show Login)->|a|
        }}}
        '''
        content = content.strip().replace('\n', ', ')
        return '<img src="http://yuml.me/diagram/scruffy/activity/' + content + '" />'
    
    # Note that there's no need to HTML escape the returned data,
    # as the template engine (Genshi) will do it for us.
