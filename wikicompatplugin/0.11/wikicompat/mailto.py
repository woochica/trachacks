from trac.core import *
from trac.wiki.api import IWikiMacroProvider, WikiSystem
import re

__all__ = ['MailToMacro']

class MailToMacro(Component):
    """Obscures an email address (somewhat).  
    {{{
    [[MailTo(somebody AT gmail DOT com)]]
    }}}
    Produces a mailto:somebody@gmail.com  link if the viewer is logged in,
    <somebody AT gmail DOT com> if not.
    """

    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'MailTo'

    def expand_macro(self, formatter, name, txt):

        txt = txt.replace('"','')
        req = formatter.req
        context = formatter.context
        if 'WIKI_ADMIN' in req.perm(context.resource):          
            r = re.compile(r'(.+?)\sAT\s(.+?)\sDOT\s(.+)',re.IGNORECASE)
            m = r.search(txt)
            if m:
                return "<a href=\"mailto:%s@%s.%s\">%s@%s.%s</a>"%\
                        (m.group(1),m.group(2),m.group(3),
                         m.group(1),m.group(2),m.group(3))
            else:
                return txt
        else:
            return '&lt;'+txt+'&gt;'
        
