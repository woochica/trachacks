"""A simple captcha to allow anonymous ticket changes as long as the user solves
a math problem.

I thought that the ITicketManipulator prepare_ticket method would be the place
to add extra HTML stuff to the ticket page, but it seems to be for future use
only.  The only way I found that I could add to the HTML was by modifying the
Genshi template using the ITemplateStreamFilter.

I looked at http://trac-hacks.org/wiki/BlackMagicTicketTweaksPlugin for help
trying to understand how the Genshi transformation stuff worked.

Author: Rob McMullen <robm@users.sourceforge.net>
License: Same as Trac itself
"""
import random
import sys
import time
import urllib

from trac.core import *
from trac.ticket.api import ITicketManipulator
from trac.web.api import ITemplateStreamFilter
from trac.wiki.api import IWikiPageManipulator

from genshi.builder import tag
from genshi.filters.transform import Transformer

class MathCaptchaPlugin(Component):
    implements(ITicketManipulator, ITemplateStreamFilter, IWikiPageManipulator)
    
    timeout = 600 # limit of 10 minutes to process the page

    def __init__(self):
        self.keys = {}
        self.last = 0

    def get_content(self):
        var1 = random.randint(1,10)
        var2 = random.randint(1,10)
        self.last += 1
        key = str(self.last)
        self.keys[key] = (var1, var2, time.time())
        
        # A little fun obfuscation: use "hoomin" instead of "human" to perhaps
        # avoid alerting spam harvesters that something neat is going on.
        content = tag.div()(
            tag.label('Anonymous users are allowed to post by solving this little equation: %d + %d = ' % (var1, var2)) + tag.input(type='text', name='hoomin_check', class_='textwidget', size='5') + tag.input(type='hidden', name='hoomin_key', value=str(key))
            )
        return content

    def validate_mathcaptcha(self, req):
        # keys older than the specified timeout get deleted
        [self.keys.pop(k) for k, (var1, var2, timestamp) in self.keys.items() 
         if time.time() - timestamp >= self.timeout]
        
        if req.authname == "anonymous":
            key = req.args.get('hoomin_key')
            if key not in self.keys:
                return [(None, "Took too long to submit page.  Please submit again.")]
            var1, var2, timestamp = self.keys.pop(key)
            hoomin = req.args.get('hoomin_check')
            #print("var1=%d var2=%d hoomin=%s" % (var1, var2, hoomin))
            try:
                hoomin = int(hoomin)
                if (var1 + var2) != hoomin:
                    self.env.log.error("%s %s %s%s: Error in math solution: %d + %d != %d author=%s comment:\n%s" % (req.remote_addr, req.remote_user, req.base_path, req.path_info, var1, var2, hoomin, req.args.get('author'), req.args.get('comment')))
                    return [(None, "Incorrect solution -- try solving the equation again!")]
            except:
                self.env.log.error("%s %s %s%s: Bad digits: '%s' author=%s comment:\n%s" % (req.remote_addr, req.remote_user, req.base_path, req.path_info, hoomin, req.args.get('author'), req.args.get('comment')))
                return [(None, "Anonymous users are only allowed to post by solving the math problem at the bottom of the page.")]

        return []


    # ITemplateStreamFilter interface

    def filter_stream(self, req, method, filename, stream, data):
        """Return a filtered Genshi event stream, or the original unfiltered
        stream if no match.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the template
        to be rendered, `stream` is the event stream and `data` is the data for
        the current template.

        See the Genshi documentation for more information.
        """

        #self.env.log.info(filename)
        if filename in ["ticket.html", "wiki_edit.html"] and data['authname'] == 'anonymous':
            # Insert the math question right before the submit buttons
            stream = stream | Transformer('//div[@class="buttons"]').before(self.get_content())
        return stream
    
    
    # ITicketManipulator interface
    
    def validate_ticket(self, req, ticket):
        """Validate a ticket after it's been populated from user input.
        
        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with the
        ticket. Therefore, a return value of `[]` means everything is OK."""
        return self.validate_mathcaptcha(req)
    
    # IWikiPageManipulator interface
    
    def validate_wiki_page(self, req, page):
        """Validate a wiki page after it's been populated from user input.
        
        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with the
        ticket. Therefore, a return value of `[]` means everything is OK."""
        return self.validate_mathcaptcha(req)
