from trac.core import Component, implements
from trac.config import Option, IntOption
from trac.web import IRequestFilter
from trac.wiki import parse_args
from trac.web.chrome import ITemplateProvider, add_stylesheet
from pkg_resources import resource_filename
from trac.web.api import ITemplateStreamFilter
from genshi.builder import tag
from genshi.filters.transform import Transformer
import re

class BreadCrumbsSystem(Component):
    implements(IRequestFilter, ITemplateProvider, ITemplateStreamFilter)
    
    ignore_pattern = Option('breadcrumbs', 'ignore pattern', None, 
        doc="""Resource names that match this pattern will not be added to 
        the breadcrumbs trail.""")
    
    max_crumbs = IntOption('breadcrumbs', 'max crumbs', 6, 
        doc="""Indicates the maximum number of breadcrumbs to store per user.""")
    
    compiled_ignore_pattern = None
    
    ## IRequestFilter
    
    def pre_process_request(self, req, handler):
        return handler
        
    def _get_crumbs(self, req):
        sess = req.session

        crumbs = []
        if 'breadcrumbs list' in sess:
            raw = sess['breadcrumbs list']
            try:
                crumbs = [x.replace('@COMMA@', ',') for x in raw.split(',')]
            except:
                pass
        
        return crumbs
        
    def post_process_request(self, req, template, data, content_type):
        if self.compiled_ignore_pattern is None:
            self.compiled_ignore_pattern = re.compile(self.ignore_pattern)
            
        try:
            path = req.path_info
            if path.count('/') >= 2:
                _, realm, rest = path.split('/', 2)
                
                if realm in ('wiki', 'ticket', 'milestone'):            
                    if '#' in rest:
                        name = rest[0:rest.index('#')]
                    else:
                        name = rest
                    
                    if '&' in name:
                        name = name[0:name.index('&')]
                    
                    id = name
                    if realm == "ticket":
                        name = "#" + name
                     
                    if self.compiled_ignore_pattern and self.compiled_ignore_pattern.match(id):
                        return template, data, content_type
                    
                    sess = req.session
                    
                    crumbs = self._get_crumbs(req)
                    
                    current = "%s:%s" % (name, req.href("%s/%s" % (realm, id)))
                    if current not in crumbs:
                        crumbs.insert(0, current)
                        crumbs = crumbs[0:self.max_crumbs]
                    else:
                        crumbs.remove(current)
                        crumbs.insert(0, current)

                    sess['breadcrumbs list'] = ','.join(
                        x.replace(',', '@COMMA@') for x in crumbs
                    )
        except:
            self.log.exception("Breadcrumb failed :(")
        

        return template, data, content_type
    
    ## ITemplateProvider
    
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('breadcrumbs', resource_filename(__name__, 'htdocs'))]
          
    def get_templates_dirs(self):
        return []

    ## ITemplateStreamFilter
    
    def filter_stream(self, req, method, filename, stream, data):
        crumbs = self._get_crumbs(req)
        if not crumbs:
            return stream
            
        add_stylesheet(req, 'breadcrumbs/css/breadcrumbs.css')
        li = []

        href = req.href(req.base_path)
        
        for crumb in crumbs:
            title, link = crumb.split(':', 1)
            li.append(
                tag.li(
                    tag.a(title=title, href=link,
                    )(title)
                )
            )
            
        insert = tag.ul(class_="nav", id="breadcrumbs")(tag.lh("Breadcrumbs:"), li)

        return stream | Transformer('//div[@id="metanav"]/ul').after(insert)
        