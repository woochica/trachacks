# Created by Noah Kantrowitz on 2008-05-16.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.
import itertools
import re


from trac.core import *
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.config import Option, OrderedExtensionsOption
from genshi.builder import tag
from genshi.filters.transform import Transformer
from pkg_resources import resource_filename

from hackergotchi.api import IHackergotchiProvider

class HackergotchiModule(Component):
    """A stream filter to add hackergotchi emblems to the timeline."""

    providers = OrderedExtensionsOption('hackergotchi', 'providers', 
                                        IHackergotchiProvider,
                                        default='GravatarHackergotchiProvider, IdenticonHackergotchiProvider')

    implements(ITemplateStreamFilter, ITemplateProvider)
    
    anon_re = re.compile('([^<]+?)\s+<([^>]+)>', re.U)
    
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if req.path_info.startswith('/timeline'):
            closure_state = [0]            
            cache = {}
            def f(stream):
                # Update the closed value
                n = closure_state[0]
                closure_state[0] += 1
                
                # Extract the user information
                author = data['events'][n]['author'].strip()
                user_info = cache.get(author)
                if user_info is not None:
                    author, name, email = user_info
                else:
                    db = self.env.get_db_cnx()
                    user_info = self._get_info(author, db)
                    cache[author] = user_info
                    author, name, email = user_info
                
                # Try to find a provider
                for provider in self.providers:
                    href = provider.get_hackergotchi(req.href, author, name, email)
                    if href is not None:
                        break
                else:
                    href = req.href.chrome('hackergotchi', 'default.png')
                
                # Build our element
                elm = tag.img(src=href, alt='Hackergotchi for %s'%author, 
                              class_='hackergotchi') 
                
                # Output the combined stream
                return itertools.chain(elm.generate(), stream)
            
            stream |= Transformer('//div[@id="content"]/dl/dt/a/span[@class="time"]').filter(f)
            add_stylesheet(req, 'hackergotchi/hackergotchi.css')
        return stream
    
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        yield 'hackergotchi', resource_filename(__name__, 'htdocs')
            
    def get_templates_dirs(self):
        #return [resource_filename(__name__, 'templates')]
        return []
    
    # Internal methods
    def _get_info(self, author, db):
        if author == 'anonymous':
            # Don't even bother trying for "anonymous"
            return author, None, None
        
        md = self.anon_re.match(author)
        if md:
            # name <email>
            return 'anonymous', md.group(1), md.group(2)
        
        cursor = db.cursor()        
        cursor.execute('SELECT name, value FROM session_attribute WHERE sid=%s AND authenticated=%s',
                       (author, 1))
        rows = cursor.fetchall()
        if rows:
            # Authenticated user, with session
            name = email = None
            for key, value in rows:
                if key == 'name':
                    name = value
                elif key == 'email':
                    email = value
            if name or email:
                return author, name, email
            else:
                return author, None, None
        
        # Assume anonymous user from this point on
        if '@' in author:
            # Likely an email address
            return 'anonymous', None, author
        
        # See if there is a default domain
        domain = self.config.get('notification', 'smtp_default_domain')
        if domain and ' ' not in author:
            return author, None, author+'@'+domain
        
        return 'anonymous', author, None
