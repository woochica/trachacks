from trac.core import Component, implements
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.web.href import Href
from trac.util.html import Markup


class TemplateProvider(Component):
    implements(ITemplateProvider)

    # ITemplateProvider#get_htdocs_dirs
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tracwysiwyg', resource_filename(__name__, 'htdocs'))]

    # ITemplateProvider#get_templates_dirs
    def get_templates_dirs(self):
        return []


class WysiwygWikiFilter(Component):
    implements(IRequestFilter)

    # IRequestFilter#pre_process_request
    def pre_process_request(self, req, handler):
        return handler

    # IRequestFilter#post_process_request
    def post_process_request(self, req, template, content_type):
        add_stylesheet(req, 'tracwysiwyg/wysiwyg.css')
        href = Href(req.base_path).chrome('tracwysiwyg/wysiwyg.js')
        script_tag = '<script type="text/javascript" charset="utf-8" src="%s"></script>'
        footer = req.hdf['project.footer'] + script_tag % href
        req.hdf['project.footer'] = Markup(footer)
        return (template, content_type)


