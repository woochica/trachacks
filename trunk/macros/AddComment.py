# vim: expandtab
from trac.Wiki import WikiPage
import trac.perm
import time
from StringIO import StringIO
from trac.WikiFormatter import wiki_to_html
from trac.util import TracError

def execute(hdf, args, env):
    authname = hdf.getValue("trac.authname", "anonymous")
    db = env.get_db_cnx()
    perm = trac.perm.PermissionCache(db, authname)
    pagename = hdf.getValue("args.page", "WikiStart")
    page = WikiPage(pagename, None, perm, db)
    wikipreview = hdf.getValue("args.preview", "")
    readonly = int(hdf.getValue("wiki.readonly", "0"))

    if readonly and not perm.has_permission(trac.perm.WIKI_ADMIN):
        raise TracError('Error: Insufficient privileges to AddComment')

    disabled = ''
    comment = hdf.getValue("args.addcomment", "")
    preview = hdf.getValue("args.previewaddcomment", "")
    cancel = hdf.getValue("args.canceladdcomment", "")
    submit = hdf.getValue("args.submitaddcomment", "")

    out = StringIO()
    if wikipreview or not perm.has_permission(trac.perm.WIKI_MODIFY):
        disabled = ' disabled'

    # If we are submitting or previewing, inject comment as it should look
    if comment and (preview or submit):
        if preview:
            out.write("<div class='wikipage' id='preview'>\n")
        out.write("<h4>Comment by %s on %s</h4>\n<p>\n%s\n</p>\n" % (authname, time.strftime('%c', time.localtime()), wiki_to_html(comment, hdf, env, db)))
        if preview:
            out.write("</div>\n")

    # When submitting, inject comment before macro
    if comment and submit:
        newtext = StringIO()
        for line in page.text.splitlines():
            if line.find('[[AddComment') == 0:
                newtext.write("==== Comment by %s on %s ====\n%s\n\n" % (authname, time.strftime('%c', time.localtime()), comment))
            newtext.write(line + "\n")
        page.set_content(newtext.getvalue())
        # TODO: How do we get remote_addr from a macro?
        page.commit(authname, 'Comment added', None)
        comment = ""

    out.write("<form name='addcomment' action='%s' method='post'>\n" % env.href.wiki(pagename))
    out.write("<fieldset>\n<legend>Add comment</legend>\n")
    out.write("<textarea name='addcomment' cols='80' rows='5' wrap='soft'%s>" % disabled)
    if wikipreview:
        out.write("Preview...")
    elif not cancel:
        out.write(comment)
    out.write("</textarea>\n")
    out.write("<br>\n")
    out.write("<input type='submit' name='submitaddcomment' value='Add comment'%s>\n" % disabled)
    out.write("<input type='submit' name='previewaddcomment' value='Preview comment'%s>\n" % disabled)
    out.write("<input type='submit' name='canceladdcomment' value='Cancel'%s>\n" % disabled)
    out.write("<script type='text/javascript'>\naddWikiFormattingToolbar(document.getElementById('addcomment'));\n</script>\n")
    out.write("</fieldset>\n</form>\n")
    return out.getvalue()# + "<pre>" + hdf.dump() + "</pre>"
