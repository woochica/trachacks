
from genshi import HTML
from genshi.builder import tag
from genshi.filters import Transformer
from genshi.filters.transform import StreamBuffer
from trac.config import Option
from trac.core import Component, implements
from trac.util.translation import domain_functions
from trac.web.chrome import add_stylesheet, add_script, ITemplateProvider
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from pkg_resources import resource_filename #@UnresolvedImport
import os

# domain name has to be the same entry_points, described in setup.py
_, tag_, N_, add_domain = \
    domain_functions('ticketnav', '_', 'tag_', 'N_', 'add_domain')

class TextAreaDescription(Component):
    """Shows next to a text area 
(like description itself or any custom description) 
an description for what the field is for.

Default values for options:
{{{
[ticket]
description_descr = 
descr_template = <div style="white-space: normal; height: 250px; 
overflow:scroll;" class="system-message">%s<div>
}}}
    """
    implements(ITemplateStreamFilter, IRequestFilter, ITemplateProvider)
    
    description_descr = Option('ticket', 'description_descr', '',
        """Explaination of description.""")
    descr_template = Option('ticket', 'descr_template',
        '<div style="white-space: normal; width: 250px; height: 250px; '
        'overflow:scroll;" class="%s">%s<div>',
        """Explaination of description.""")
       
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html':
#            print "_____________ am in TextAreaDescription"
            fields = data['fields']
            if self.description_descr:
#                print "having description_descr: %s" % self.description_descr
#                print "having description_template: %s" % self.descr_template
                html_d = self.descr_template % \
                    ('ticket-rndescr', self.description_descr)
                stream |= Transformer('.//th/label[@for="field-description"]')\
                    .after(HTML(html_d))
                
            for f in fields:
                if f['skip'] or not f['type'] == 'textarea':
                    continue 
                 
                descr = self.config.get('ticket-custom', '%s.descr' % f['name'])
                if descr:
#                    print "processing field %s" % f
                    css_class = self.config.get('ticket-custom','%s.css_class'\
                                                 % f['name'])
#                    print css_class
                    field_name = 'field-%s' % f['name']
                    tr_str = './/label[@for="%s"]' % field_name
                    html = self.descr_template % (css_class, descr)
                    stream |= Transformer(tr_str).after(HTML(html))
        return stream
    
    # IRequestHandler methods
    def pre_process_request(self, req, handler):        
        return handler
    #==========================================================================
    # Add JavaScript an an additional css to ticket template
    #==========================================================================
#    def post_process_request(self, req, template, data, content_type):
#        if req.path_info .startswith('/newticket')or \
#            req.path_info .startswith('/ticket'):
#            add_stylesheet(req, 'ticketnav/css/ticket_descr.css')
#        return template, data, content_type
    def post_process_request(self, req, template, data, content_type):
        if req.path_info .startswith('/newticket') or \
            req.path_info .startswith('/ticket'):
            add_stylesheet(req, 'hw/css/ticket_descr.css')
        return template, data, content_type
    
    def get_templates_dirs(self):
        return #[resource_filename(__name__, 'templates')]
    
    def get_htdocs_dirs(self):
        return [('hw', resource_filename(__name__, 'htdocs'))]

class CssTemplate(Component):
    """Add links to style sheets located in templates folder.

[http://en.wikipedia.org/wiki/Cascading_Style_Sheets CSS] files 
started with `"all_templates"` are added for all Trac sites. 
CSS files starting with template name (without `.html`-suffix) 
are added for specific template.

To apply changes you need to restart the server. 

Examples for files which resides in projects `templates` folder:
|| `all_templates_general.css` || added to all Trac sites ||
|| `ticket_additional.css` || only added for `ticket.html` pages || 
"""
    implements(IRequestFilter, ITemplateProvider)
    
    _init_done = False
    _css_dict = {}
    
    # IRequestHandler methods
    def pre_process_request(self, req, handler):
        self.log.debug('pre_process_request')
        return handler

    def post_process_request(self, req, template, data, content_type):
        if not self._init_done:
            self._init_done = self._do_init(req, template)
            self.log.info('initialized CSS dictionary: %s ' % self._css_dict)
        
        if self._css_dict.has_key(template):
            for css_file in self._css_dict[template]:
                add_stylesheet(req, css_file)
        
        if self._css_dict.has_key('*'):
            for css_file in self._css_dict['*']:
                add_stylesheet(req, css_file)
                
        return template, data, content_type
        
    def _do_init(self, req, template):
        template_dir = self.env.get_templates_dir()
        
        if os.access(template_dir, os.R_OK):
            for file in os.listdir(template_dir):
                file_name = str(file)
                if file_name and file_name.lower().endswith('.css'):
                    templ_name = self._extract_template_name(file_name)
                    if templ_name:
                        css_file = "css_templates/%s" % (file_name)
                        if self._css_dict.has_key(templ_name):
                            self._css_dict[templ_name].append( css_file )
                        else:
                            self._css_dict[templ_name] = [ css_file]
        else:
            self.log.warn('could not read template dir!')
                
        return True
    
    # ITemplateProvider methods
    def get_templates_dirs(self):
        return
    
    def get_htdocs_dirs(self):
        template_dir = self.env.get_templates_dir()
        return [('css_templates', template_dir)]
    
    
    def _extract_template_name(self, file_name):
        """extracts template name to indicate 
        for which template the CSS should be"""
        templ_name = None
        if not file_name:
            return None
        
        if file_name.lower().startswith('all_templates'):
            templ_name = "*"
        else: 
            idx = file_name.find("_")
            if idx != -1:
                templ_name = file_name[0:idx]
                templ_name += ".html"
        return templ_name

    
class CustomizedTicketView(Component):
    """Small changes of ticket view.

Concretely:
 * disables field `field-reporter`, so it cannot be changed anymore
 * disables button `Reply`, so no comment could be made to any description
"""
    implements(ITemplateStreamFilter)
    
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html':
            stream |= Transformer('.//input[@id="field-reporter"]') \
                .attr('disabled', 'disabled')
            stream |= Transformer('.//form[@id="addreply"]') \
                .attr('style', 'display: none')
        return stream

    
class SortMilestoneVersion(Component):
    """Sorts drop-down lists of version and milestone regardless of the case and 
make milestone a must field, when a default milestone is set.

Default behavior of Trac for sorting milestones is:
{{{
inbox, v1, v2, Inbox, V1, V2
}}}

This plugin sorts it as following:
{{{
inbox, Inbox, v1, V1, v2, V2
}}}
"""
    implements (ITemplateStreamFilter)
    
    #ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):
        if filename and (filename == 'ticket.html' or filename == 'newticket'):
#            print "filename '%s' matches" % filename
            if not data:
                return stream
            try:
                fields = data['fields']
                if not fields:
                    return stream
                version = self.get_field_list(fields, 'version')
                version['options'].sort(key=unicode.lower)
                
                milestones = self.get_field_list(fields, 'milestone')
                if self.config.get('ticket', 'default_milestone'):
                    milestones['optional'] = False
                    
                for opt in milestones['optgroups']:
                    opt['options'].sort(key=unicode.lower)
                    
            except Exception, e:
                self.log.error('error has occured by sorting: %s' % e)
        return stream
        
    def get_field_list(self, fields, fieldname):
        if not fields or not fieldname:
            return None
        for fld in fields:
            if fld['name'] == fieldname:
                return fld

                    
class TicketNavigation(Component):
    """Implements an extra Navigation menu
by dividing the main ticket information in
an several div areas an providing a "jump-to" to
the anker with are represented in the navigation box.

'''ATTENTION:''' This plugin might raises in some cases an error. 
Thus this component should not be used yet.
 
This code fragment is evil, since it raises an error on imported umlauts:
{{{
newStream = HTML(stream)
}}}
"""  
    implements(ITemplateStreamFilter, IRequestFilter, ITemplateProvider) 
            
    css_banner_top1 = tag.div(id_='top1')
    css_banner_top2 = tag.div(id_='top2')
    css_banner_top3 = tag.div(id_='top3')
    css_banner_top4 = tag.div(id_='top4')
    css_left = tag.div(id_='left')

    # ITemplateStreamFilter methods
    #self.log.debug("Filer: %r", filter) oder print
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html' or filename == 'newticket':
            stream = self.__getAnchors(stream)
            stream = self._customize_View(stream)
            return stream
        return stream
                  
    # IRequestHandler methods
    def pre_process_request(self, req, handler):        
        return handler

    #===========================================================================
    # Add JavaScript an an additional css to ticket template
    #===========================================================================
    def post_process_request(self, req, template, data, content_type):
        if req.path_info .startswith('/newticket')or \
            req.path_info .startswith('/ticket'):
            add_script(req, 'hw/js/scrollup.js')
            add_stylesheet(req, 'hw/css/navstyle.css')
        return template, data, content_type
    
    #==========================================================================
    # ITemplateProvider methods
    # Used to add the plugin's templates and htdocs 
    #==========================================================================
    def get_templates_dirs(self):
        return #[resource_filename(__name__, 'templates')]
    
    def get_htdocs_dirs(self):
        return [('hw', resource_filename(__name__, 'htdocs'))]   
    
#===============================================================================
# Private Methods
#===============================================================================
   
    #===========================================================================
    # Search for the defined anchors in the webdocume, in order to print them
    # in the document navigation menue
    #===========================================================================
    def __getAnchors(self, stream):
        #=======================================================================
        # this code fragment is evil, since it raises an error on 
        # imported umlauts:
        # newStream = HTML(stream)
        #
        # *** tried also this, but didn't work:
        #newStream = stream.select('//h1 [@id="trac-ticket-title"]//a/text()')
        #
        # *** tried also:
        #stream_str = '%s' % stream
        #stream_str = stream_str.encode('utf-8')
        #self.log.info("stream: ")
        #self.log.info(stream_str)
        #newStream = HTML(stream_str)
        #
        # *** tried also:
        #test = Path('//h1 [@id="trac-ticket-title"]//a/text()').test()
        #namespaces, variables = {}, {}
        #head = ''
        #for event in stream:
        #    if test(event, namespaces, variables):
        #        self.log.info('%s: %s' % (event[0], event[1]))
        #        print('%s %r' % (event[0], event[1]))
        #        if event[0] == 'TEXT':
        #            if isinstance(event[1], Markup): 
        #                head += event[1].striptags()
        #            else:
        #                head += event[1]
        #        #START (QName('child'), Attrs([(QName('id'), u'2')]))
        #print "namespaces, variables; head: %s, %s; %s" % \ 
        #     (namespaces, variables, head)
        #======================================================================
        newStream = HTML(stream)
        self.anchors = {}
        self.keylist = []
        #headline
        headline = newStream.select('//h1 [@id="trac-ticket-title"]//a/text()')
        if headline:
            for item in headline:
                self.anchors[item[1]] = ''
                self.keylist.append(item[1])

        #further entities
        list = newStream.select('//h2 [@class="foldable"]/text()')
        if list:
            for index, item in enumerate(list):
                self.anchors[item[1]] = "no%s" % str(index + 1)
                self.keylist.append(item[1])
        list = newStream.select('//form [@id="propertyform"]//fieldset/@id')
        
        #comment
        comment = newStream.select('//h2 [@id="trac-add-comment"]//a/text()')        
        for com in comment:
            self.anchors[com[1]] = "comment"
            self.keylist.append(com[1])

        return newStream
     
    #==========================================================================
    # Customize the Ticket view to provide an frame like look an additional
    # document navigation menue 
    #==========================================================================
    def _customize_View(self, stream):

        filter = Transformer('.//div [@id="banner"]')
        stream = stream | filter.wrap(self.css_banner_top2)
          
        buffer = StreamBuffer();
        stream = stream | Transformer('.//div [@id="banner"]').copy(buffer) \
              .end().select('.//div [@id="top2"]') \
              .after(tag.div(id_='top1')(buffer))
                
        filter = Transformer('.//div [@id="mainnav"]')
        stream = stream | filter.wrap(self.css_banner_top4)
            
        buffer = StreamBuffer()
        stream = stream | Transformer('.//div [@id="mainnav"]').copy(buffer) \
              .end().select('.//div [@id="top4"]') \
              .after(tag.div(id_='top3')(buffer))    
        
        filter = Transformer('.//div [@id="top3"]');
        stream = stream | filter.after(tag.div(id_='right')(tag.p()))
        
        filter = Transformer('.//div [@id="right"]')  
        stream = stream | filter. \
            append(tag.div(class_='wiki-toc')(tag.h4(_('Table of Contents'))))   
        
        # just for the menu / TOC
        filter = Transformer('.//div [@class="wiki-toc"]')
        
        if self.anchors and self.keylist:
            for key in self.keylist:
                stream = stream | filter.append(tag.a(key,
                                          href='#' + self.anchors.get(key),
                                          onclick="scrollup();") + tag.br())
        filter = Transformer('.//div [@id="main"]')
        stream = stream | filter.wrap(self.css_left)
            
        return stream;



#===============================================================================
# DEPRECATED COMPONENTS
#===============================================================================
   
class HtmlContent(Component):
    """DEPRECATED

'''Deprecated - use [http://ckeditor.com/ CKEditor]-Plugin instead! '''
Enables HTML content in description, adding Javascript editor and 
adding additional CSS file for manipulation CSS declarations.

Options:
|| '''option name''' || '''values''' || '''description''' ||
|| description_format || `wiki` | `html` || format for ticket description (default: '''wiki''') ||
|| editor_source || valid path || Usually it should stored in project or common js folder. For ckeditor for example it could be site/js/ckeditor/ckeditor.js. ||
|| editor_replace || valid path || Javascript, which should replace textareas. ||
|| additional_css || valid path || Path to additional css file, which overrides css-declarations. ||

Sample configuration:
{{{
[ticket]
description_format = html
editor_source = site/js/ckeditor/ckeditor.js
editor_replace = <script type="text/javascript">CKEDITOR.replace('@FIELD_NAME@', {toolbar: 'custom'});</script>
additional_css = site/css/add_ticket.css
}}}

In above sample configuration [http://ckeditor.com/ CKEditor] is used as online editor and 
the editor source is located in projects-folder `htdocs/js/ckeditor`,
after each `textarea` with HTML-Option content of `editor_replace` will be added.
The file in option `additional_css` will be added and therefore will override these declarations.

'''Attention:''' To have a correct preview, file `ticket_box.html` has to be edited:
{{{
1 <py:if test="field">
2   <py:choose test="">
3     <py:when test="ticket[field.name] and field.format == 'html'">${wiki_to_html(context, '{{{ \n#!html \n' + ticket[field.name]  + '\n}}}', escape_newlines=preserve_newlines)}</py:when>
4     <py:when test="'rendered' in field">${field.rendered}</py:when>
5     <py:otherwise>${ticket[field.name]}</py:otherwise>
6   </py:choose>
7 </py:if>
}}} 

Line 3 has to be inserted into `py:choose` block in above template-snippet.

{{{
<div py:if="ticket.description" class="searchable" xml:space="preserve">
<py:choose>
    <py:when test="description_format == 'html'">${wiki_to_html(context, '{{{ \n#!html \n' + ticket.description  + '\n}}}', escape_newlines=preserve_newlines)}</py:when>
    <py:otherwise>${wiki_to_html(context, ticket.description, escape_newlines=preserve_newlines)}</py:otherwise>
</py:choose>
</div>
}}}

Also `py:choose` block has to be added into div-block near the end of file 
(see above template-snippet)."""
    implements(IRequestFilter, ITemplateStreamFilter)
    
    description_format = Option('ticket', 'description_format', '',
        """Format of description.
        Empty or wiki is Trac Standard; html formats description as HTML.""")
    
    additional_css_file = Option('ticket', 'additional_css', '',
        """Path to additional css file, which overrides css-declarations.""")
    
    editor_source = Option('ticket', 'editor_source', '',
        """Path to javascript editor.
        Usually it should stored in project or common js folder.
        For ckeditor for example it could be site/js/ckeditor/ckeditor.js.""")
    
    editor_replace = Option('ticket', 'editor_replace', '',
        """Javascript, which should replace textareas.""")
    
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if data and template == 'ticket.html':
            data['description_format'] = self.description_format
            if self.editor_source:
                add_script(req, self.editor_source)
            if self.additional_css_file:
                add_stylesheet(req, self.additional_css_file)
        return template, data, content_type
    
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html' and self.editor_source \
            and self.editor_replace:
            self.log.debug ("further processing: template %s, "
                            "editor-source %s, editor-replace %s" % \
                            (filename, self.editor_source, self.editor_replace))
            
            # check if description should be in HTML
            if self.description_format == "html":
                add_editor = self.editor_replace \
                    .replace("@FIELD_NAME@", "field_description")
                html = HTML(add_editor)
                self.log.debug ("add_editor is %s" % add_editor)
                stream |= Transformer('.//textarea[@name="field_description"]').after(html)
            fields = data['fields']
            for f in fields:
                if f['skip'] or not f['type'] == 'textarea' or not f.has_key('format') or not f['format'] == 'html':
                    continue 
                # only textarea-fields with format HTML should be processed at this point
                field_name = 'field_%s' % f['name']
                add_editor = self.editor_replace.replace("@FIELD_NAME@", field_name)
                html = HTML(add_editor)
                tr_str = './/textarea[@name="%s"]' % field_name
                self.log.debug ("add_editor for field %s is %s; tr_str is %s" % (field_name, add_editor, tr_str))
                stream |= Transformer(tr_str).after(html)
            
        return stream
       


#===============================================================================
# UNUSED COMPONENTS
# These components are not used yet, because they are not working and
# are only made because in a research manner.
#===============================================================================


#===============================================================================
#class FileUploader(Component): 
#    """Test for uploading images by CKEditor"""
#    implements (IAttachmentChangeListener, IAttachmentManipulator, IRequestHandler)
#    
#    def match_request(self, req):
#        """Return whether the handler wants to process the given request."""
#        return re.match(r'/image_upload', req.path_info)
#
#    def process_request(self, req):
#        """Process the request.
#
#        For ClearSilver, return a `(template_name, content_type)` tuple,
#        where `template` is the ClearSilver template to use (either a
#        `neo_cs.CS` object, or the file name of the template), and
#        `content_type` is the MIME type of the content.
#
#        For Genshi, return a `(template_name, data, content_type)` tuple,
#        where `data` is a dictionary of substitutions for the template.
#
#        For either templating systems, "text/html" is assumed if `content_type`
#        is `None`.
#
#        Note that if template processing should not occur, this method can
#        simply send the response itself and not return anything.
#        """
#        print "========= ____  [process_request]"
#        if ( req.path_info == "/image_upload" ):
#            add_stylesheet(req, 'hw/css/style.css')
#            print "========= ____  [process_request] correct path ... doing more"
#            data = {}
#            return 'ticketnav/image-uploader.html', data, None
#        
#    def prepare_attachment(self, req, attachment, fields):
#        """Not currently called, but should be provided for future
#        compatibility."""
#        print "--------------.... [prepare_attachment] try to add attachment"
#        
#    def validate_attachment(self, req, attachment):
#        """Validate an attachment after upload but before being stored in Trac
#        environment.
#        
#        Must return a list of `(field, message)` tuples, one for each problem
#        detected. `field` can be any of `description`, `username`, `filename`,
#        `content`, or `None` to indicate an overall problem with the
#        attachment. Therefore, a return value of `[]` means everything is
#        OK."""
#        print "_______________.... [validate_attachment] try to add attachment"
#        return []
#        
#    def attachment_added(self, attachment):
#        """Called when an attachment is added."""
#        print "_______________ [attachment_added] try to add attachment"
#        print "_______________ [attachment_added] add attachment: %s" % attachment
##        return attachment
#
#    def attachment_deleted(self, attachment):
#        """Called when an attachment is deleted."""
#        print "_______________ [attachment_deleted] try to delete attachment"
##        return attachment
#
#    def attachment_reparented(self, attachment, old_parent_realm, old_parent_id):
#        """Called when an attachment is reparented."""
#        print "_______________ [attachment_reparented] add attachment: %s" % attachment
#        return attachment, old_parent_realm, old_parent_id
#===============================================================================


#===============================================================================
# Tested if copying ticket-box.html is working, but it is not!
#===============================================================================
#class HtmlContent(Component):
#    implements (IRequestFilter)
#    """Allow description and other textarea-fields having HTML-content"""
#    
#    # IRequestHandler methods
##    def match_request(self, req):
##        print "===== HtmlContent, path_info: %s" % req.path_info
##        return re.match(r'/(ticket|newticket)(?:_trac)?(?:/.*)?$', req.path_info)
#        
#    def pre_process_request(self, req, handler):
#        return handler
#    
#    # IRequestHandler methods
#    def post_process_request(self, req, template, data, content_type):
#        print "template: %s" % template
#        self._check_init()
##        data = {}
##        return handler
##        return 'ticket.html', data, None
#        return template, data, content_type
#
#    
#    def _check_init(self):
#        """First check if Plugin has already been initialized. 
#        """
#        
#        print "====== _check_init" 
#        
#        template_path = self.env.path
#            
#        if template_path and template_path.endswith('/'):
#            template_path += 'templates'
#        else:
#            template_path += '/templates'
#        
#        if os.access(template_path, os.W_OK):
#            print "can write to path %s" % template_path
#            from pkg_resources import resource_filename
##            src_name = resource_filename(__name__, 'templates/ticket-box.html')
#            src_name = resource_filename(__name__, 'templates')
#            print "src_name: %s" % src_name
#            shutil.copy(src_name + '/ticket-box.html', template_path + '/ticket-box.html')
#        elif os.access(template_path, os.R_OK):
#            print "can read to path %s" % template_path
#            
#        print "template_path: %s" % template_path