# -*- coding: utf-8 -*-

from string import lower
import pkg_resources

from genshi import HTML
from genshi.filters import Transformer
from genshi.core import Markup
from trac.core import * 
from trac.web.chrome import add_stylesheet, add_script, add_script_data, ITemplateProvider
from trac.web.api import ITemplateStreamFilter, IRequestHandler
from trac.config import Option, ChoiceOption, ListOption
from trac.mimeview.api import Context
from trac.resource import Resource
from trac.wiki.formatter import format_to, Formatter, _markup_to_unicode,\
    WikiProcessor
from trac.wiki.parser import WikiParser
from StringIO import StringIO
import os

__all__ = ['CkIntegrationModule']

# copied from format_to_html in formatter.py
def format_to_cke_html(env, context, wikidom, accepted_code_processors, escape_newlines=None):
    if not wikidom:
        return Markup()
    if escape_newlines is None:
        escape_newlines = context.get_hint('preserve_newlines', False)
    return CKEditorFormatter(env, context, wikidom, accepted_code_processors).generate(escape_newlines)


class CKEditorFormatter(Formatter):
    """Extends base wiki formatter by setting code processor's name 
for code blocks. Thus CKEditor can save it, so it could be processed 
later by format processor like Pygments (see TracSyntaxColoring). 
"""
    
    data_code_style = None
    
    def __init__(self, env, context, wikidom, accepted_code_processors):
        self.env = env
        self.context = context
        self.accepted_code_processors = accepted_code_processors
        if isinstance(wikidom, basestring):
            wikidom = WikiParser(env).parse(wikidom)
        self.wikidom = wikidom
        Formatter.__init__(self, env, context)

    # copied from HtmlFormatter
    def generate(self, escape_newlines=False):
        """Generate HTML elements.

        newlines in the wikidom will be preserved if `escape_newlines` is set.
        """
        # FIXME: compatibility code only for now
        out = StringIO()
        self.format(self.wikidom, out, escape_newlines)
#        self.env.log.debug('generated html: %s' % out.getvalue())
        return Markup(out.getvalue())
    
    def handle_code_block(self, line, startmatch=None):
        """Overrides Formatter.handle_code_block, so it 
adds an additional `pre`-tag with attribute `data-code-style`,  
in which the code-format is saved.

Furthermore the code block is converted into HTML, because otherwise CKEditor 
ignores empty lines. In this method linebreaks `\n` are replaced by `<br/>`.
"""
        handle_code_style = False
        if line.strip() == WikiParser.ENDBLOCK and self.code_processor: 
            clean_processor_name = self.code_processor.name
            self.env.log.debug('clean_processor_name: %s' %  clean_processor_name) 
            
            idx = clean_processor_name.find('; ')
            if idx >= 0:
                clean_processor_name = clean_processor_name[:idx]
            
            if clean_processor_name == 'default':
                handle_code_style = True
                self.data_code_style = ''
            elif clean_processor_name not in ['diff', 'td']:
                try:
                    from pygments.lexers import get_lexer_for_mimetype
                    
                    lexer = get_lexer_for_mimetype(clean_processor_name)
                    proc_aliases = lexer.aliases
                    if proc_aliases and len(proc_aliases) > 0:
                        clean_processor_name = proc_aliases[0]
                    else:
                        clean_processor_name = lexer.name
                    
                    if clean_processor_name in self.accepted_code_processors:
                        self.data_code_style = ' data-code-style="%s"' % clean_processor_name
                        handle_code_style = True
                except Exception, e:
                    self.env.log.warn( "Error when retrieving lexer by mimetype: %s" % e )
                    self.data_code_style = ''
                
        if handle_code_style:
            self.env.log.debug('processing self.data_code_style: %s' %  self.data_code_style) 
            code_text = os.linesep.join(self.code_buf)
            html_text = WikiProcessor(self, 'default').process(code_text)
            html_text = _markup_to_unicode( html_text )
            html_text = html_text.replace('\n', '<br/>')
            
            html = HTML( html_text )
            html |= Transformer('//pre').unwrap()
            buffer = StringIO()
            html.render(out=buffer, encoding='utf-8')
            
            self.out.write( '<pre%s>' % self.data_code_style )
            self.out.write( _markup_to_unicode( buffer.getvalue() ) )
            self.out.write('</pre>')
            
            self.in_code_block = 0
        else:
            Formatter.handle_code_block(self, line, startmatch)
        

class CkIntegrationModule(Component):
    """CKEditor integration for Trac
    
    Replace wiki-textareas in Trac with the CKEditor, as a fully-featured rich editor.
    
    Adds a request handler for AJAX-based TracWiki->HTML rendering.
    
    The plugin supports several modes of integration, determined by the 
    `editor_type` option (see Configuration section).
    
    The CKEditor itself is not built into the plugin, in order to allow the administrator
    to choose the layout and configuration freely ('''note that CKEditor >= 3.6 is required''').
    Use the `editor_source` option to determine the actual location of the editor.
    
    '''Disclaimer:''' This plugin is under development, and the `full_integration` mode
    is known to be experimental (at best) - only a handful of elements are supported.
    Feel free to join the effort to enhance the `full_integration` at
    http://trac-hacks.org/wiki/CkEditorPlugin.
    
    Configuration (config name, description, default values):
    [[TracIni(ckeditor)]]"""
    implements(ITemplateProvider, ITemplateStreamFilter, IRequestHandler)
    
    editor_type = ChoiceOption('ckeditor', 'editor_type',
        ['full_integration', 'only_ticket', 'only_wiki', 'html_wrapper', 'none'],
        """Type of integrated editor. Possible types are: 
`full_integration`: CKEditor with TracWiki output ('''experimental'''), 
`only_ticket`: CKEditor with TracWiki output for ticket fields ('''experimental'''); ''leaves wiki editing as in Trac standard'', 
`only_wiki`: CKEditor with TracWiki output for wiki pages ('''experimental'''); ''leaves ticket editing as in Trac standard'',
`html_wrapper`: CKEditor with HTML output wrapped in html-processor,  
`none`: No integration - ''leaves editing as in Trac standard''""")
    
    editor_source = Option('ckeditor', 'editor_source', 'site/js/ckeditor/ckeditor.js',
        """Path to CKEditor 3.6.x javascript source.
        
        The path should be specified as viewed by the client,
        and must be accessible by the client-browser.
        
        A recommended setup involves installing CKEditor in the htdocs/js directory
        of the Trac environment, and setting this option to site/js/ckeditor/ckeditor.js.""")
    
    code_styles = ListOption('ckeditor', 'code_styles', 'cpp, csharp, java, js, python, sql, default, xml',
        doc="""List of code styles, which should be processed by CKEditor and 
        displayed in CKEditor dialog 'insert code'.""")
    
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

    def _check_editor_type(self, filename):
        """Checks whether editor is enabled for this view (filename).
        Returns `true` if it is enabled, otherwise `false`.
"""
        if not self.editor_type or 'none' == self.editor_type:
            return False
        elif 'only_ticket' == self.editor_type:
            return lower(filename) == 'ticket.html'
        elif 'only_wiki' == self.editor_type:
            return lower(filename) == 'wiki_edit.html'
        else:
            return lower(filename) in self.template_fields
    
    def get_styles_list(self):
        style_list = [ ]
        if self.code_styles:
            style_opt_list = self.code_styles
            self.log.info('self.code_styles: %s' % style_opt_list)
            for style in style_opt_list:
                if style == 'default':
                    style_list.append(['Text', ''])
                    continue
                
                try:
                    from pygments.lexers import get_lexer_by_name    
                    lexer = get_lexer_by_name(style)
                    style_list.append([lexer.name, style])
                except Exception, e:
                    self.log.warn( "Error when retrieving lexer by name: %s" % e )
        return style_list
                    
    # ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):
        self.log.debug("ckintegration: template %s" % (filename))
        # Act only when enabled, and editor_source defined, and current template has wiki-textareas
        if self.editor_source and self._check_editor_type(filename):
            # Some javascript global variable to add to the response to assist to tracwiki plugin
            
            add_script_data(req, {
                            'ck_editor_type': self.editor_type,
                            'ck_code_styles': self.get_styles_list(),
                            'trac_base_url':  req.href.base,
                            'ck_tracwiki_path': req.href.chrome('ckintegration'),
                            'ck_resource_realm': 'wiki',
                            'ck_resource_id': '',
                            'form_token': req.form_token,
                            })
            # Load the needed scripts (CKEditor itself, and the tracwiki plugin
            add_script(req, self.editor_source)
            add_script(req, 'ckintegration/tracwiki.js')
            add_script(req, 'ckintegration/pastecode.js')
            # Inject a script that adds the tracwiki plugin as an external plugin to CKEditor
            # @todo: Perform init with a dedicated loader script
            # @todo: Use the init to modify the CKEditor toolbar
            ck_plugin_init = '<script type="text/javascript">CKEDITOR.plugins.addExternal("tracwiki", ck_tracwiki_path, "tracwiki.js");\n'
            ck_plugin_init += 'CKEDITOR.plugins.addExternal("pastecode", ck_tracwiki_path, "pastecode.js");</script>'
            stream |= Transformer('.//body').prepend(HTML(ck_plugin_init))
            #add_script(req, 'ckintegration/ckloader.js')
            # Replace all relevant textarea fields in the template with CKEditor instances
            for field_name in self.template_fields[lower(filename)]:
                self.log.debug('Replacing textarea "%s" with CKEditor instance' % (field_name))
                add_editor = '''<script type="text/javascript">
                    CKEDITOR.replace("%s", { extraPlugins : "tracwiki,pastecode" });
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
                    self.log.debug('Replacing textarea "%s" with CKEditor instance' % (field_name))
                    add_editor = '''<script type="text/javascript">
                        CKEDITOR.replace("%s", { extraPlugins : "tracwiki,pastecode" });
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
        rendered = format_to_cke_html(self.env, context, text, self.code_styles, **options)
        
        # since Trac renders underlined text as `<span class="underlined">text</span>
        # instead of u-tag, we need to adjust it for compatibility's sake
        # see also discussion at Google Groups:
        # https://groups.google.com/group/trac-dev/browse_thread/thread/833206a932d1f918
        html = HTML(rendered)
        html |= Transformer('//span[@class="underline"]').rename('u').attr('class', None)
        # CKEditor renders indentation by using p style="margin-left: 40px" 
        # instead of blockquote-tag
        html |= Transformer('//blockquote/p').attr('style', 'margin-left: 40px')
        html |= Transformer('//blockquote').unwrap()
        buffer = StringIO()
        html.render(out=buffer, encoding='utf-8')
        req.send( buffer.getvalue() )
        