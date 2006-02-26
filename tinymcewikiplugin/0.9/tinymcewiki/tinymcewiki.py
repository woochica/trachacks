# -*- coding: iso8859-1 -*-
# TinyMCE Wiki plugin
#

import os
from StringIO import StringIO

from trac.core import *
from trac.wiki.api import IWikiMacroProvider 
from trac.util import enum, escape, format_datetime, get_reporter_id, \
                      pretty_timedelta, shorten_line
from trac.wiki.web_ui import WikiModule
from trac.wiki.formatter import wiki_to_html, wiki_to_oneliner
from trac.web.chrome import ITemplateProvider, add_stylesheet

from trachtml import TracHTMLParser,WikiToEditorHtmlFormatter



class TracHtmlToHtml(Component):
    implements(IWikiMacroProvider)
    """
    This is processer which convert trachtml to html.
    """

    """Extension point interface for components that provide Wiki macros."""

    def get_macros(self):
        """Return an iterable that provides the names of the provided macros."""
        yield 'trachtml'

    def get_macro_description(self,name):
        """Return a plain text description of the macro with the specified name.
        """
        return inspect.getdoc(RecentChangesMacro)

    def render_macro(self,req, name, content):
        """Return the HTML output of the macro."""
        db = self.env.get_db_cnx()

        parser = TracHTMLParser()
        parser.clear()
        parser.set_traclink_mode(True,False)
        parser.env = self.env
        parser.req = req
        parser.log = self.log
        parser.db = db
        parser.feed(content)
        retvalue = ''.join(parser.get_outputs())
        parser.close()

        return retvalue


class TinyMceWikiPlugin(WikiModule):
    implements(ITemplateProvider)
    """
    This is main module of TinyMCE Wiki Plugin.
    """


    def _transrate_trachtml(self,req,db,data,can_process,can_wrap):

        parser = TracHTMLParser()
        parser.clear()
        parser.set_traclink_mode(can_process,can_wrap)
        parser.env = self.env
        parser.req = req
        parser.log = self.log
        parser.db = db
        parser.feed(data)
        datas = parser.get_outputs()
        retvalue = ''.join(datas)
        parser.close()
        parser = None

        return retvalue


    def editorhtml_to_trachtml(self,req,db,data):
        # convert wraped TracLink,TracMacro to unwaped TracLink,TracMacro 
        return self._transrate_trachtml(req,db,data,False,False)

    def trachtml_to_editorhtml(self,req,db,data):
        # convert wraped TracLink,TracMacro to unwaped TracLink,TracMacro 
        # and re-wrap TracLink,TracMacro
        return self._transrate_trachtml(req,db,data,False,True)

    def editorhtml_to_html(self,req,db,data):
        # convert wraped TracLink,TracMacro to unwaped TracLink,TracMacro 
        # and process TracLink,TracMacro to html
        return self._transrate_trachtml(req,db,data,True,False)
    
    def wiki_to_editorhtml(self,req, db,data):
        # convert wiki to html which wraped TracLink,TracMacro
        out = StringIO()
        WikiToEditorHtmlFormatter(self.env, req, 0, db).format(data, out, False)
        retvalue = out.getvalue()

        out.close()
        return retvalue


    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [self.env.get_templates_dir(),
                self.config.get('trac', 'templates_dir'),
                resource_filename(__name__, 'templates')]
    
    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)
    
        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []
    #    #from pkg_resources import resource_filename
    #    #return [('tm',resource_filename(__name__, 'tinymce'))]
    #    from pkg_resources import resource_filename
    #    return [self.env.get_templates_dir(),
    #            self.config.get('trac', 'templates_dir'),
    #            resource_filename(__name__, 'templates')]
                

    
    # IRequestHandler methods

    def process_request(self, req):
        self.log.debug('TinyMceWiki:process_request')
        #for tynimce
        if req.args.get('editor') == 'tinymce':
            req.hdf['wiki.editor'] = 'tinymce' 
            req.hdf['wiki.hoge'] = 'TinyMceWiki' 

        WikiModule.process_request(self, req)
        return 'tinymcewiki.cs',None
        
    def _do_save(self, req, db, page):
        if page.readonly:
            req.perm.assert_permission('WIKI_ADMIN')
        elif not page.exists:
            req.perm.assert_permission('WIKI_CREATE')
        else:
            req.perm.assert_permission('WIKI_MODIFY')

        page.text = req.args.get('text')

        #from tinymce 
        editor = req.args.get('editor') #
        if (req.method=='POST')and(editor == 'tinymce'): 
            page.text = '{{{'+os.linesep+'#!trachtml'+os.linesep + self.editorhtml_to_trachtml(req,db,page.text) + os.linesep + '}}}' 
            # todo:convert trachtml to wiki and save
            # page.text = self.editorhtml_to_wiki(req, db,page.text)


        if req.perm.has_permission('WIKI_ADMIN'):
            # Modify the read-only flag if it has been changed and the user is
            # WIKI_ADMIN
            page.readonly = int(req.args.has_key('readonly'))

        page.save(req.args.get('author'), req.args.get('comment'),
                  req.remote_addr)
        req.redirect(self.env.href.wiki(page.name))

    def _render_editor(self, req, db, page, preview=False):
        req.perm.assert_permission('WIKI_MODIFY')

        if req.args.has_key('text'):
            page.text = req.args.get('text')
        if preview:
            page.readonly = req.args.has_key('readonly')

        #for tynimce
        editor = req.args.get('editor') #

        #make source fot tinyMce
        edit_source = page.text
        if (editor == 'tinymce'): # tinymce edit -> edit,preview
            if req.method=='POST':
                # from editor
                edit_source = self.trachtml_to_editorhtml(req, db,edit_source)
                self.log.debug("edit->edit");
            else:
                # from db
                lines = edit_source.splitlines()
                if len(lines) >= 3 and lines[0] == '{{{' : #and lines[1] == '#!trachtml':
                    #edit_source = 
                    self.log.debug("DBtrac->edit");
                    edit_source = self.trachtml_to_editorhtml(req, db, ''.join(lines[2:-1]))
                else:
                    self.log.debug("DBwiki->edit");
                    edit_source = self.wiki_to_editorhtml(req, db,edit_source)
                #todo: convert trachtml to wiki
                #   edit_source = wiki_to_trachtml(self.editorhtml_to_wiki(req, db,page.text)
        
        
        author = req.args.get('author', get_reporter_id(req))
        comment = req.args.get('comment', '')
        editrows = req.args.get('editrows')
        if editrows:
            pref = req.session.get('wiki_editrows', '20')
            if editrows != pref:
                req.session['wiki_editrows'] = editrows
        else:
            editrows = req.session.get('wiki_editrows', '20')

        req.hdf['title'] = escape(page.name) 
        info = {
            'page_name': page.name,
            'page_source': escape(edit_source), #for TyniMCE (page.text->edit_source)
            'version': page.version,
            'author': escape(author),
            'comment': escape(comment),
            'readonly': page.readonly,
            'edit_rows': editrows,
            'scroll_bar_pos': req.args.get('scroll_bar_pos', '')
        }
        if page.exists:
            info['history_href'] = escape(self.env.href.wiki(page.name,
                                                             action='history'))
        if preview:
            if (editor == 'tinymce'): # tinymce edit -> edit,preview
                info['page_html'] = wiki_to_html('{{{'+os.linesep+'#!trachtml'+os.linesep+page.text+os.linesep+'}}}', self.env, req, db)
                #todo: convert trachtml to wiki
                #  info['page_html'] = wiki_to_html(self.editorhtml_to_wiki(req, db,page.text)
            else:
                info['page_html'] = wiki_to_html(page.text, self.env, req, db)
            info['readonly'] = int(req.args.has_key('readonly'))
        req.hdf['wiki'] = info

