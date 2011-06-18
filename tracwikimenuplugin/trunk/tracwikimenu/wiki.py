from trac.core import *
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_stylesheet, add_script, ITemplateProvider
from trac.resource import get_resource_description
from genshi.filters.transform import Transformer
from genshi.builder import tag
from trac.wiki.api import WikiSystem


from tracresourcetools.relation.api import ResourceRelationSystem  

class WikiMenuHandler(Component):
    implements(ITemplateStreamFilter, ITemplateProvider)
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('wikimenu', resource_filename(__name__, 'htdocs'))]
    def get_templates_dirs(self):
        return []
    
    def filter_stream(self, req, method, filename, stream, data):
        
        if req.path_info.startswith('/wiki/'):
            if data and data.has_key('page') and hasattr(data['page'], 'resource'):
                title = data['title']
                filter = Transformer('//div[@id="pagepath"]')
                filter = filter.empty()
                filter = filter.append( tag.a( 'wiki:', href = req.href.wiki(), class_ = 'pathentry first' ) )
               
                resource = data['page'].resource
                relation_system = ResourceRelationSystem(self.env)
                tree = relation_system.get_cached_tree(req)    
                add_stylesheet(req, 'wikimenu/css/superfish.css')
                add_script(req, 'wikimenu/js/jquery.bgiframe.min.js')
                add_script(req, 'wikimenu/js/superfish.js')
                add_script(req, 'wikimenu/js/popup.js')
                resources = []
                for res in relation_system.get_ancestors(resource, tree=tree):
                    resources.append(res)
                for res in reversed( resources ):
                    label = get_resource_description(self.env, res)
                    if res.realm=='wiki':
                        if res.id and WikiSystem(self.env).has_page(res.id):
                            
                            menu = tag.ul( )
                                                        
                            for res_child in relation_system.get_children(res):
                                child_label = get_resource_description(self.env, res_child)
                                if res_child.realm=='wiki':
                                    if res_child.id and WikiSystem(self.env).has_page(res_child.id):
                                        anc = tag.a(child_label, href = req.href.wiki(child_label))
                                        menu.append(tag.li( anc ))
                                        
                            
                            filter = filter.append( tag.ul( tag.li( 
                                tag.a(label, href=req.href.wiki(label) ),
                                    menu ), class_= 'wiki_menu' ) )
                            if title != label:
                                filter = filter.append( tag.span( ' / ', 
                                        class_ = 'pathentry sep' ) )
                remove_tran = '//a[@title="View ' + title + '"]'
                return stream | filter
        return stream
