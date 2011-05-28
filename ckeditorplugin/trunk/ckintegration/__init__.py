# -*- coding: utf-8 -*-

from string import lower
import pkg_resources

from genshi import HTML
from genshi.filters import Transformer
from trac.core import * 
from trac.web.chrome import add_stylesheet, add_script, add_script_data, ITemplateProvider
from trac.web.api import ITemplateStreamFilter, IRequestHandler
from trac.config import Option, ChoiceOption
from trac.mimeview.api import Context
from trac.resource import Resource
from trac.wiki.formatter import format_to

__all__ = ['CkIntegrationModule']

class CkIntegrationModule(Component):
    """CKEditor integration for Trac
    
    Replace wiki-textareas in Trac with the CKEditor, as a fully-featured rich editor.
    
    Adds a request handler for AJAX-based TracWiki->HTML rendering.
    
    The plugin supports 3 modes of integration, determined by the `editor_type` option.
    
    The CKEditor itself is not built into the plugin, in order to allow the administrator
    to choose the layout and configuration freely ('''note that CKEditor >= 3.6 is required''').
    Use the `editor_source` option to determine the actual location of the editor.
    
    '''Disclaimer:''' This plugin is under development, and the `full_integration` mode
    is known to be experimental (at best) - only a handful of elements are supported.
    Feel free to join the effort to enhance the `full_integration` at
    http://trac-hacks.org/wiki/CkEditorPlugin."""
    implements(ITemplateProvider, ITemplateStreamFilter, IRequestHandler)
    
    editor_type = ChoiceOption('ckeditor', 'editor_type',
        ['html_wrapper', 'full_integration', 'none'],
        """Type of integrated editor.
        || `html_wrapper` || CKEditor with HTML output wrapped in html-processor ||
        || `full_integration` || CKEditor with TracWiki output (experimental) ||
        || `none` || No integration - plain old textarea ||""")
    
    editor_source = Option('ckeditor', 'editor_source', 'site/js/ckeditor/ckeditor.js',
        """Path to CKEditor 3.6.x javascript source.
        
        The path should be specified as viewed by the client,
        and must be accessible by the client-browser.
        
        A recommended setup involves installing CKEditor in the htdocs/js directory
        of the Trac environment, and setting this option to site/js/ckeditor/ckeditor.js.""")
    
#    editor_replace = Option('ckeditor', 'editor_replace', '',
#        """Javascript, which should replace textareas.""")
    
    template_fields = {
        'ticket.html': ('field_description', 'comment', ),
        'wiki_edit.html': ('text', ),
        'admin_components.html': ('description', ),
        'admin_milestones.html': ('description', ),
        'admin_versions.html': ('description', ),
        }

    # ITemplateProvider
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ckintegration', resource_filename(__name__, 'htdocs'))]

    # ITemplateProvider
    def get_templates_dirs(self):
        return []

    # ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):
        self.log.debug("ckintegration: template %s" % (filename))
        # Act only when enabled, and editor_source defined, and current template has wiki-textareas
        if 'none' != self.editor_type and self.editor_source and lower(filename) in self.template_fields:
            # Some javascript global variable to add to the response to assist to tracwiki plugin
            add_script_data(req, {
                            'ck_editor_type': self.editor_type,
                            'ck_render_url':  req.href.ck_wiki_render(),
                            'ck_tracwiki_path': req.href.chrome('ckintegration'),
                            'ck_resource_realm': 'wiki',
                            'ck_resource_id': '',
                            'form_token': req.form_token,
                            })
            # Load the needed scripts (CKEditor itself, and the tracwiki plugin
            add_script(req, self.editor_source)
            add_script(req, 'ckintegration/tracwiki.js')
            # Inject a script that adds the tracwiki plugin as an external plugin to CKEditor
            # @todo: Perform init with a dedicated loader script
            # @todo: Use the init to modify the CKEditor toolbar
            ck_plugin_init = '<script type="text/javascript">CKEDITOR.plugins.addExternal("tracwiki", ck_tracwiki_path, "tracwiki.js");</script>'
            stream |= Transformer('.//body').prepend(HTML(ck_plugin_init))
            #add_script(req, 'ckintegration/ckloader.js')
            # Replace all relevant textarea fields in the template with CKEditor instances
            for field_name in self.template_fields[lower(filename)]:
                self.log.info('Replacing textarea "%s" with CKEditor instance' % (field_name))
                add_editor = '''<script type="text/javascript">
                    CKEDITOR.replace("%s", { extraPlugins : "tracwiki" });
                </script>''' % (field_name)
                #self.log.debug ("add_editor is %s" % add_editor)
                stream |= Transformer('.//textarea[@name="%s"]' % (field_name)).after(HTML(add_editor))
            # Also replace custom textarea fields in the ticket template that have wiki format 
            if 'ticket.html' == lower(filename) and 'fields' in data:
                for f in data['fields']:
                    if f['skip'] or not lower(f['type']) == 'textarea' or   \
                            not f.has_key('format') or not 'wiki' == lower(f['format']):
                        continue 
                    field_name = 'field_%s' % f['name']
                    self.log.info('Replacing textarea "%s" with CKEditor instance' % (field_name))
                    add_editor = '''<script type="text/javascript">
                        CKEDITOR.replace("%s", { extraPlugins : "tracwiki" });
                    </script>''' % (field_name)
                    stream |= Transformer('.//textarea[@name="%s"]' % (field_name)).after(HTML(add_editor))
        return stream

    # IRequestHandler
    def match_request(self, req):
        return req.path_info == '/ck_wiki_render'

    # IRequestHandler
    def process_request(self, req):
        # Allow all POST requests (with a valid __FORM_TOKEN, ensuring that
        # the client has at least some permission). Additionally, allow GET
        # requests from TRAC_ADMIN for testing purposes.
        if req.method != 'POST':
            req.perm.require('TRAC_ADMIN')
            
        # @todo: Embed "tips" within the rendered output for the editor
        # (recognize TracLinks, table-stuff, macros, processors)
        # @todo: Save the content in server-side user-specific field for recovery
        
        realm = req.args.get('realm', 'wiki')
        id = req.args.get('id')
        version = req.args.get('version')
        if version is not None:
            try:
                version = int(version)
            except ValueError:
                version = None
        text = req.args.get('text', '')
        flavor = req.args.get('flavor')
        options = {}
        if 'escape_newlines' in req.args:
            options['escape_newlines'] = bool(int(req.args['escape_newlines']
                                                  or 0))
        if 'shorten' in req.args:
            options['shorten'] = bool(int(req.args['shorten'] or 0))
        
        resource = Resource(realm, id=id, version=version)
        context = Context.from_request(req, resource)
        rendered = format_to(self.env, flavor, context, text, **options)
        req.send(rendered.encode('utf-8'))
