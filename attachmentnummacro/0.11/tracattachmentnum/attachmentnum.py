"""
tracattachmentnum:
a plugin for Trac
http://trac.edgewall.org
"""

from trac.core import *
from trac.resource import *

from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import format_to_oneliner
from trac.wiki.macros import WikiMacroBase,parse_args


class AttachmentNumMacro(WikiMacroBase):
    implements(IWikiMacroProvider)

    ### methods for IWikiMacroProvider
    def expand_macro(self, formatter, name, content):
        largs, kwargs = parse_args(content)
        try:
            num = int(largs[0]) - 1
        except:
            raise TracError("Argument must be a positive integer!")
        if num < 0:
            raise TracError("Argument must be a positive integer!")

        option = self.env.config.get
        raw    = self.env.config.getbool('attachmentnum', 'raw', False)
        if 'raw' in kwargs:
            vraw = str(kwargs['raw']).lower()
            if vraw in ('yes','true','1','on'):
                raw = True
            elif vraw in ('no','false','0','off'):
                raw = False

        id = get_resource_name(self.env, formatter.resource)
        type = formatter.resource.realm

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute( "SELECT filename FROM attachment WHERE type='%s' " \
                        "AND id='%s' ORDER BY time;" % (type,id) )

        attmnts = cursor.fetchall()
        if len(attmnts) < num + 1 or not attmnts[num] or not attmnts[num][0]:
            raise TracError("Attachment #%i doesn't exists!" % (num+1))
        filename = attmnts[num][0]

        wikilink = "attachment:'" + filename + "'"
        if raw:
            wikilink = "raw-" + wikilink
        if kwargs.get('format', option('attachmentnum', 'format')) == 'short':
            wikilink = "[%s %s]" % (wikilink,filename)
        return format_to_oneliner(self.env, formatter.context, wikilink)


