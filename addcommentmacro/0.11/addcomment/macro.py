# vim: expandtab
import re, time
from StringIO import StringIO

from genshi.builder import tag

from trac.core import *
from trac.wiki.formatter import format_to_html
from trac.util import TracError
from trac.util.text import to_unicode
from trac.web.chrome import add_link, add_script
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage


class AddCommentMacro(WikiMacroBase):
    """A macro to add comments to a page. Usage:
    {{{
    [[AddComment]]
    }}}
    The macro accepts one optional argument that allows appending
    to the wiki page even though user may not have modify permission:
    {{{
    [[AddComment(appendonly)]]
    }}}
    """
    
    def expand_macro(self, formatter, name, content):
        
        args, kw = parse_args(content)
        req = formatter.req
        context = formatter.context
        
        # Prevent multiple inclusions - store a temp in req
        if hasattr(req, 'addcommentmacro'):
            raise TracError('\'AddComment\' macro cannot be included twice.')
        req.addcommentmacro = True
        
        # Prevent it being used outside of wiki page context
        resource = context.resource
        if not resource.realm == 'wiki':
            raise TracError('\'AddComment\' macro can only be used in Wiki pages.')
        
        # Setup info and defaults
        authname = req.authname
        page = WikiPage(self.env, resource)
        page_url = req.href.wiki(resource.id)
        wikipreview = req.args.get("preview", "")
        appendonly = ('appendonly' in args)
        # Can this user add a comment to this page?
        cancomment = not page.readonly
        # Is this an "append-only" comment or are we an administrator?
        if 'WIKI_ADMIN' in req.perm(resource) or appendonly:
            cancomment = True
        if not cancomment:
            raise TracError('Error: Insufficient privileges to AddComment')
        disabled = False
        
        # Get the data from the POST
        comment = req.args.get("addcomment", "")
        preview = req.args.get("previewaddcomment", "")
        cancel = req.args.get("canceladdcomment", "")
        submit = req.args.get("submitaddcomment", "")
        if not cancel and req.authname == 'anonymous':
            authname = req.args.get("authoraddcomment", authname)
        
        # Ensure [[AddComment]] is not present in comment, so that infinite
        # recursion does not occur.
        comment = to_unicode(re.sub('(^|[^!])(\[\[AddComment)', '\\1!\\2', comment))
        
        the_preview = the_message = the_form = tag()
        
        if wikipreview or not ('WIKI_MODIFY' in req.perm(resource) or appendonly):
            disabled = True
        
        # If we are submitting or previewing, inject comment as it should look
        if cancomment and comment and (preview or submit):
            heading = tag.h4("Comment by ", authname, " on ",
                        to_unicode(time.strftime('%c', time.localtime())),
                        id="commentpreview")
            if preview:
                the_preview = tag.div(heading,
                                format_to_html(self.env, context, comment),
                                class_="wikipage", id="preview")
        
        # When submitting, inject comment before macro
        if comment and submit:
            submitted = False
            newtext = ""
            for line in page.text.splitlines():
                if line.find('[[AddComment') == 0:
                    newtext += "==== Comment by %s on %s ====\n%s\n\n" % (
                            authname,
                            to_unicode(time.strftime('%c', time.localtime())),
                            comment)
                    submitted = True
                newtext += line+"\n"
            if submitted:
                page.text = newtext
                page.save(authname, 'Comment added', req.environ['REMOTE_ADDR'])
                req.warning("Comment saved.")
                req.redirect(page_url)
            else:
                the_message = tag.div(tag.strong("ERROR: "), "[[AddComment]] "
                          "macro call must be the only content on its line. "
                          "Could not add comment.",
                          class_="system-message")

        the_form = tag.form(
                    tag.fieldset(
                        tag.legend("Add comment"),
                        tag.div(
                            (wikipreview and "Page preview..." or None),
                            tag.textarea((not cancel and comment or ""),
                                        class_="wikitext",
                                        id="addcomment",
                                        name="addcomment",
                                        cols=80, rows=5,
                                        disabled=(disabled and "disabled" or None)),
                            class_="field"
                        ),
                        (req.authname == 'anonymous' and tag.div(
                            tag.label("Your email or username:",
                                    for_="authoraddcomment"),
                            tag.input(id="authoraddcomment", type="text",
                                    size=30, value=authname)
                        ) or None),
                        tag.div(
                            tag.input(value="Add comment", type="submit",
                                    name="submitaddcomment", size=30,
                                    disabled=(disabled and "disabled" or None)),
                            tag.input(value="Preview comment", type="submit",
                                    name="previewaddcomment",
                                    disabled=(disabled and "disabled" or None)),
                            tag.input(value="Cancel", type="submit",
                                    name="canceladdcomment",
                                    disabled=(disabled and "disabled" or None)),
                            class_="buttons"
                        ),
                    ),
                    method="post",
                    action=page_url+"#commenting",
                )
        
        add_script(req, 'common/js/wikitoolbar.js')

        return tag.div(the_preview, the_message, the_form, id="commenting")
    
    def process_macro_post(self, req):
        self.log.debug('AddCommentMacro: Got a POST')

