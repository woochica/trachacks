# vim: expandtab
from trac.Wiki import WikiPage
import trac.perm
import time
from StringIO import StringIO
from trac.WikiFormatter import wiki_to_html
from trac.util import TracError
import re

def execute(hdf, args, env):
    authname = hdf.getValue("trac.authname", "anonymous")
    db = env.get_db_cnx()
    perm = trac.perm.PermissionCache(db, authname)
    pagename = hdf.getValue("args.page", "WikiStart")
    page = WikiPage(pagename, None, perm, db)
    wikipreview = hdf.getValue("args.preview", "")
    appendonly = (args == 'appendonly')
    readonlypage = int(hdf.getValue("wiki.readonly", "0"))
    # Can this user add a comment to this page?
    cancomment = not readonlypage
    # Is this an "append-only" comment or are we an administrator?
    if perm.has_permission(trac.perm.WIKI_ADMIN) or appendonly:
        cancomment = True

    if not cancomment:
        raise TracError('Error: Insufficient privileges to AddComment')

    disabled = ''
    comment = hdf.getValue("args.addcomment", "")
    preview = hdf.getValue("args.previewaddcomment", "")
    cancel = hdf.getValue("args.canceladdcomment", "")
    submit = hdf.getValue("args.submitaddcomment", "")
    if not cancel:
        authname = hdf.getValue("args.authoraddcomment", authname)

    # Ensure [[AddComment]] is not present in comment, so that infinite
    # recursion does not occur.
    comment = re.sub('(^|[^!])(\[\[AddComment)', '\\1!\\2', comment)

    out = StringIO()
    if wikipreview or not perm.has_permission(trac.perm.WIKI_MODIFY):
        disabled = ' disabled="disabled"'

    # If we are submitting or previewing, inject comment as it should look
    if cancomment and comment and (preview or submit):
        if preview:
            out.write("<div class='wikipage' id='preview'>\n")
        out.write("<h4 id='commentpreview'>Comment by %s on %s</h4>\n<p>\n%s\n</p>\n" % (authname, time.strftime('%c', time.localtime()), wiki_to_html(comment, hdf, env, db)))
        if preview:
            out.write("</div>\n")

    # When submitting, inject comment before macro
    if comment and submit:
        submitted = False
        newtext = StringIO()
        for line in page.text.splitlines():
            if line.find('[[AddComment') == 0:
                newtext.write("==== Comment by %s on %s ====\n%s\n\n" % (authname, time.strftime('%c', time.localtime()), comment))
                submitted = True
            newtext.write(line + "\n")
        if submitted:
            # XXX Is this the dodigest hack ever? This is needed in 
            # "appendonly" mode when the page is readonly. XXX
            if appendonly:
                perm.expand_meta_permission('WIKI_ADMIN');
            page.set_content(newtext.getvalue())
            # TODO: How do we get remote_addr from a macro?
            page.commit(authname, 'Comment added', None)
            comment = ""
        else:
            out.write("<div class='system-message'><strong>ERROR: [[AddComment]] macro call must be the only content on its line. Could not add comment.</strong></div>\n")

    out.write("<form action='%s#commentpreview' method='post'>\n" % env.href.wiki(pagename))
    out.write("<fieldset>\n<legend>Add comment</legend>\n")
    out.write("<div class='field'>\n<textarea id='addcomment' name='addcomment' cols='80' rows='5'%s>" % disabled)
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
    out.write("<script type='text/javascript'>\naddWikiFormattingToolbar(document.getElementById('addcomment'));\n</script>\n")
    out.write("</fieldset>\n</form>\n")
    return out.getvalue()# + "<pre>" + hdf.dump() + "</pre>"
