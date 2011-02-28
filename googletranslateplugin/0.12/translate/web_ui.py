# Created by Denis Yeldandi on 2011-02-21.
# Copyright (c) 2011 Denis Yeldandi. All rights reserved.
import itertools


from trac.core import *
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script, add_script_data
from trac.config import Option, OrderedExtensionsOption
from genshi.builder import tag
from genshi.filters.transform import Transformer
from pkg_resources import resource_filename
from trac.util.translation import domain_functions
import pkg_resources 

_, tag_, N_, add_domain = domain_functions('Translate', ('_', 'tag_', 'N_', 'add_domain'))

class TranslateModule(Component):
    """A stream filter to add translate buttons."""

    implements(ITemplateStreamFilter, ITemplateProvider)
    googleApiKey = Option('translate', 'google_api_key', default='',
        doc='Google api key to use')


    def __init__(self):
        locale_dir = pkg_resources.resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if req.path_info.startswith('/ticket'):
            button = tag.div(tag.input(type="submit", title=_("Translate to %s") % req.locale.get_display_name(), value=_("Translate"), forward=_("Translate"), backward=_("Untranslate"), working=_("Working"), name="translate", class_="translate"))
            button(class_="inlinebuttons")
            script = tag.script('');
            script(src = 'https://www.google.com/jsapi?key='+self.googleApiKey)
            script(type = 'text/javascript')
            stream |= Transformer('//head').prepend(script)
            stream |= Transformer('//div[@id="content"]/div[@id="ticket"]/div[@class="description"]/h3').after(button)
            stream |= Transformer('//div[@id="content"]/div/div[@id="changelog"]/div[@class="change"]/h3').after(button)
            add_stylesheet(req, 'translate/translate.css')
            add_script_data(req, {'googleApiKey': self.googleApiKey})
            add_script_data(req, {'sessionLanguage': req.locale.language})
            add_script(req, 'translate/translate.js')
        return stream
    
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        yield 'translate', resource_filename(__name__, 'htdocs')
            
    def get_templates_dirs(self):
        return []
    
