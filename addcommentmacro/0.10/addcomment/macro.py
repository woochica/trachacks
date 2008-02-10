# vim: expandtab
from trac.core import *
from trac.wiki.macros import WikiMacroBase

import trac.perm
from StringIO import StringIO
from trac.wiki.formatter import wiki_to_html
from trac.wiki.model import WikiPage
from trac.util import Markup
from trac.util import TracError
from trac.web.chrome import add_link
from trac.util.text import to_unicode

import re, time

class AddCommentMacro(WikiMacroBase):
    """A macro to add comments to a page."""
    
    def render_macro(self, req, name, content):
        return execute(req.hdf, content, self.env)

    def _render_macro(self, req, name, content):
        pass # Fill in a deuglified version here

    def process_macro_post(self, req):
        self.log.debug('AddCommentMacro: Got a POST')
        
def execute(hdf, args, env):
    # prevents from multiple inclusions
    if hdf.has_key('addcommentmacro'):
       raise TracError('\'AddComment\' macro cannot be included twice')
    hdf['addcommentmacro'] = True

    authname = to_unicode(hdf.getValue("trac.authname", "anonymous"))
    db = env.get_db_cnx()
    perm = trac.perm.PermissionCache(env, authname)
    pagename = to_unicode(hdf.getValue("wiki.page_name", "WikiStart"))
    page = WikiPage(env, pagename, None, db)
    wikipreview = hdf.getValue("wiki.preview", "")
    appendonly = (args == 'appendonly')
    readonlypage = int(hdf.getValue("wiki.readonly", "0"))
    # Can this user add a comment to this page?
    cancomment = not readonlypage
    # Is this an "append-only" comment or are we an administrator?
    if perm.has_permission('WIKI_ADMIN') or appendonly:
        cancomment = True

    if not cancomment:
        raise TracError('Error: Insufficient privileges to AddComment')

    disabled = ''

    comment = Markup(to_unicode(hdf.getValue("args.addcomment", ""))).unescape()
    preview = hdf.getValue("args.previewaddcomment", "")
    cancel = hdf.getValue("args.canceladdcomment", "")
    submit = hdf.getValue("args.submitaddcomment", "")
    if not cancel:
        authname = to_unicode(hdf.getValue("args.authoraddcomment", authname))

    # Ensure [[AddComment]] is not present in comment, so that infinite
    # recursion does not occur.
    comment = re.sub('(^|[^!])(\[\[AddComment)', '\\1!\\2', comment)

    out = StringIO()
    if wikipreview or not (perm.has_permission('WIKI_MODIFY') or appendonly):
        disabled = ' disabled="disabled"'

    # If we are submitting or previewing, inject comment as it should look
    if cancomment and comment and (preview or submit):
        if preview:
            out.write("<div class='wikipage' id='preview'>\n")
        out.write("<h4 id='commentpreview'>Comment by %s on %s</h4>\n<p>\n%s\n</p>\n" % (
                    authname, to_unicode(time.strftime('%c', time.localtime())),
                    wiki_to_html(comment, env, None)))
        if preview:
            out.write("</div>\n")

    # When submitting, inject comment before macro
    if comment and submit:
        submitted = False
        newtext = StringIO()
        for line in page.text.splitlines():
            if line.find('[[AddComment') == 0:
                newtext.write("==== Comment by %s on %s ====\n%s\n\n" % (
                        authname, to_unicode(time.strftime('%c', time.localtime())),
                        comment))
                submitted = True
            newtext.write(line + "\n")
        if submitted:
            # XXX Is this the dodgiest hack ever? This is needed in 
            # "appendonly" mode when the page is readonly. XXX
#            if appendonly:
#                perm.expand_meta_permission('WIKI_ADMIN');
            # TODO: How do we get remote_addr from a macro?
            page.text = newtext.getvalue()
            page.save(authname, 'Comment added', None)
            comment = ""
        else:
            out.write("<div class='system-message'><strong>ERROR: [[AddComment]] macro call must be the only content on its line. Could not add comment.</strong></div>\n")

    out.write("<form action='%s#commentpreview' method='post'>\n" % env.href.wiki(pagename))
    out.write("<fieldset>\n<legend>Add comment</legend>\n")
    out.write("<div class='field'>\n<textarea class='wikitext' id='addcomment' name='addcomment' cols='80' rows='5'%s>" % disabled)
    if wikipreview:
        out.write("Page preview...")
    elif not cancel:
        out.write(comment)
    out.write("</textarea>\n")
    out.write("</div>\n")
    out.write('<div class="field">\n<label for="authoraddcomment">Your email or username:</label>\n<br/><input id="authoraddcomment" type="text" name="authoraddcomment" size="30" value="%s" />\n</div>' % authname)
    out.write("<div class='field'>\n<input size='30' type='submit' name='submitaddcomment' value='Add comment'%s/>\n" % disabled)
    out.write("<input type='submit' name='previewaddcomment' value='Preview comment'%s/>\n" % disabled)
    out.write("<input type='submit' name='canceladdcomment' value='Cancel'%s/>\n</div>\n" % disabled)
    out.write('<script type="text/javascript" src="%sjs/wikitoolbar.js"></script>' % hdf['htdocs_location'])
    out.write("</fieldset>\n</form>\n")

    return out.getvalue()# + "<pre>" + hdf.dump() + "</pre>"

