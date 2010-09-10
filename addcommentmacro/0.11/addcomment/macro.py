# vim: expandtab
import re, time
from StringIO import StringIO

from genshi.builder import tag

from trac.core import *
from trac.wiki.formatter import format_to_html
from trac.util import TracError
from trac.util.text import to_unicode
from trac.web.api import IRequestFilter, RequestDone
from trac.web.chrome import add_script
from trac.wiki.api import parse_args, IWikiMacroProvider
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule

from macropost.api import IMacroPoster

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
    implements(IWikiMacroProvider, IRequestFilter, IMacroPoster)

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
        
        # Can this user add a comment to this page?
        appendonly = ('appendonly' in args)
        cancomment = False
        if page.readonly:
            if 'WIKI_ADMIN' in req.perm(resource):
                cancomment = True
        elif 'WIKI_MODIFY' in req.perm(resource):
            cancomment = True
        elif appendonly and 'WIKI_VIEW' in req.perm(resource):
            cancomment = True
        else:
            self.log.debug('Insufficient privileges for %s to AddComment to %s',
                                   req.authname, resource.id)
        
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

        # If we are submitting or previewing, inject comment as it should look
        if cancomment and comment and (preview or submit):
            heading = tag.h4("Comment by ", authname, " on ",
                        to_unicode(time.strftime('%c', time.localtime())),
                        id="commentpreview")
            if preview:
                the_preview = tag.div(heading,
                                format_to_html(self.env, context, comment),
                                class_="wikipage", id="preview")
        
        # Check the form_token
        form_ok = True
        if submit and req.args.get('__FORM_TOKEN','') != req.form_token:
            form_ok = False
            the_message = tag.div(tag.strong("ERROR: "),
                "AddComment received incorrect form token. "
                "Do you have cookies enabled?",
                class_="system-message")
        
        # When submitting, inject comment before macro
        if comment and submit and cancomment and form_ok:
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
                
                # Let the wiki page manipulators have a look at the
                # submission.
                valid = True
                req.args.setdefault('comment', 'Comment added.')
                try:
                    for manipulator in WikiModule(self.env).page_manipulators:
                        for field, message in manipulator.validate_wiki_page(req, page):
                            valid = False
                            if field:
                                the_message += tag.div(tag.strong("invalid field '%s': " % field),
                                                       message,
                                                       class_="system-message")
                            else:
                                the_message += tag.div(tag.strong("invalid: "),
                                                       message,
                                                       class_="system-message")

                # The TracSpamfilterPlugin does not generate messages,
                # but throws RejectContent.
                except TracError, s:
                    valid = False
                    the_message += tag.div(tag.strong("ERROR: "), s, class_="system-message")

                if valid:        
                    page.save(authname, req.args['comment'], req.environ['REMOTE_ADDR'])
                    # We can't redirect from macro as it will raise RequestDone
                    # which like other macro errors gets swallowed in the Formatter.
                    # We need to re-raise it in a post_process_request instead.
                    try:
                        self.env.log.debug(
                            "AddComment saved - redirecting to: %s" % page_url)
                        req._outheaders = []
                        req.redirect(page_url)
                    except RequestDone:
                        req.addcomment_raise = True
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
                                    disabled=(not cancomment and "disabled" or None)),
                            class_="field"
                        ),
                        (req.authname == 'anonymous' and tag.div(
                            tag.label("Your email or username:",
                                    for_="authoraddcomment"),
                            tag.input(id="authoraddcomment", type="text",
                                    size=30, value=authname,
                                    name="authoraddcomment",
                                    disabled=(not cancomment and "disabled" or None))
                        ) or None),
                        tag.input(type="hidden", name="__FORM_TOKEN",
                                        value=req.form_token),
                        tag.div(
                            tag.input(value="Add comment", type="submit",
                                    name="submitaddcomment", size=30,
                                    disabled=(not cancomment and "disabled" or None)),
                            tag.input(value="Preview comment", type="submit",
                                    name="previewaddcomment",
                                    disabled=(not cancomment and "disabled" or None)),
                            tag.input(value="Cancel", type="submit",
                                    name="canceladdcomment",
                                    disabled=(not cancomment and "disabled" or None)),
                            class_="buttons"
                        ),
                    ),
                    method="post",
                    action=page_url+"#commenting",
                )

        if not wikipreview:
            # Wiki edit preview already adds this javascript file
            add_script(req, 'common/js/wikitoolbar.js')
        
        return tag.div(the_preview, the_message, the_form, id="commenting")
    
    # IMacroPoster method
    
    def process_macro_post(self, req):
        self.log.debug('AddCommentMacro: Got a POST')

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if hasattr(req, 'addcomment_raise'):
            self.env.log.debug("AddCommentMacro: Re-raising RequestDone from redirect")
            del(req.addcomment_raise)
            raise RequestDone
        return template, data, content_type
