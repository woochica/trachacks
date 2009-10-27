"""
tracattachmentnum:
a plugin for Trac
http://trac.edgewall.org
"""

from trac.core import *
from trac.resource import *

from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import format_to_oneliner
from trac.wiki.macros import parse_args

__url__      = r"$URL$"[6:-2]
__author__   = r"$Author$"[9:-2]
__revision__ = int(r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]


class AttachmentNumMacro(Component):
    """
Macro which allows to link to wiki attachment by number instead by name.

Website: http://trac-hacks.org/wiki/AttachmentNumMacro

Examples:
{{{
[[AttachmentNum(1)]]                # First attachment, result: "attachment:'first.doc'".
[[AttachmentNum(1,raw=True)]]       # First attachment (raw link), result: "raw-attachment:'first.doc'".
[[AttachmentNum(1,format=short)]]   # First attachment, hyper-linked filename is printed only, result: "first.doc".
}}}
    """
    implements(IWikiMacroProvider)

    ### methods for IWikiMacroProvider
    def get_macros(self):
      yield 'AttachmentNum'

    def get_macro_description(self, name):
      return self.__doc__

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

        res  = formatter.resource
        id   = res.id
        type = res.realm

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


