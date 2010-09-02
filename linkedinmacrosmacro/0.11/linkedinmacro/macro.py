# -*- coding: utf-8 -*-

from trac.wiki.macros import WikiMacroBase
from trac.wiki.api import parse_args
from trac.core import TracError
import uuid
 
__all__ = ['LinkedInCompanyMacro', 'LinkedInProfileMacro']

class LinkedInCompanyMacro(WikiMacroBase):
    """
    Generates a Linked-in Company Insider widget, a simple Javascript widget
    which you can place on the wiki pages to show a user how many people they
    know at any company. The user must log in LinkedIn (this can be accessed
    from the widget) and have cookies enabled. 
    
    You can put the widget on your page as many times as you want and there are
    three different presentation formats.
    
    syntax:
    {{{
        LinkedInCompany(Company Name,type=type)
    }}}
    Mandatory, possitional parameters:
      * Company name, Company Name to show in the widget.
    Optional, named parameters:
      * type, widget aspect choose from:
        - noborder
        - border
        - popup
    
    If there's no type 'noborder' is taken as default
    """
    def expand_macro(self,formatter,name,args):
        anon_params,named_params = parse_args(args)
        if len(anon_params) <> 1:
            raise TracError('Error: mandatory param, you must provide a company name.')
        corp = anon_params[0];
        
        type = named_params.pop('type', 'noborder')
        
        if type == 'noborder':
            useborder = 'no'
            jsfunc = 'CompanyInsiderBox'
        elif type == 'popup':
            useborder = 'yes'
            jsfunc = 'CompanyInsiderPopup'
        elif type == 'border':
            useborder = 'yes'
            jsfunc = 'CompanyInsiderBox'
        else:
            raise TracError('Error: Type must be one from noborder, border or popup.')
        
        span_id = str(uuid.uuid4())
        
        res = ('<script ' +
            'src="http://www.linkedin.com/companyInsider?script&useBorder=' +
            useborder + '"' + 'type="text/javascript"></script>\n' +
            '<span id="' + span_id + '"></span>\n' +
            '<script type="text/javascript">\n' +
            'new LinkedIn.'+jsfunc+'("' + span_id + '","' + corp + '");\n'+
            '</script>')
        return res;
    

class LinkedInProfileMacro(WikiMacroBase):
    """
    Macro to present and style a !LinkedIn profile url. The trac user must be
    loged in !LinkedIn and have cookies enabled.

    syntax:
    {{{
        LinkedInProfile(profile url,type=type,name=name)
    }}}
    Mandatory, possitional parameters:
      * Company name, Company Name to show in the widget.
    Optional, named parameters:
      * type, widget aspect choose from:
        - inline
        - popup
      * name: Name to present in popup mode
      
    If there's no type, popup is taken as default
    
    If there's no name, the profile url will be pressented. This only have
    effect in popup mode, because element rendered by the macro in this mode
    is a link.
    """
    
    def expand_macro(self, formatter, name, args):
        anon_params,named_params = parse_args(args)
        if len(anon_params) <> 1:
            raise TracError('Error: Mandatory parameter, you must provide a LinkedIn public profile url.')
        dude = anon_params[0]
        
        type = named_params.pop('type', 'popup')
        name = named_params.pop('name','')
        
        if not name:
            name = dude
        if not((type == 'popup') or (type == 'inline')):
            raise TracError('Error: Type must be either inline or popup.')
        
        res = ('<script type="text/javascript" src="http://www.linkedin.com/js/public-profile/widget-os.js"></script>\n'+
            '<a class="linkedin-profileinsider-' + type +
            '" href="'+ dude + '">' + name + '</a>')
        
        return res
        