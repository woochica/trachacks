"""
tracattachmentnum:
a plugin for Trac
http://trac.edgewall.org
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

from  trac.core            import  *
from  trac.wiki.api        import  IWikiMacroProvider
from  trac.wiki.formatter  import  format_to_oneliner
from  trac.wiki.macros     import  parse_args
from  trac.config          import  Option, BoolOption

class AttachmentNumMacro(Component):
    """
Macro which allows to link to wiki attachment by number instead by name.

Website: http://trac-hacks.org/wiki/AttachmentNumMacro

`$Id$`

Examples:
{{{
[[AttachmentNum(1)]]                # First attachment, result: "attachment:'first.doc'".
[[AttachmentNum(1,raw=True)]]       # First attachment (raw link), result: "raw-attachment:'first.doc'".
[[AttachmentNum(1,format=short)]]   # First attachment, hyper-linked filename is printed only, result: "first.doc".
}}}
    """
    implements ( IWikiMacroProvider )

    raw    = BoolOption('attachmentnum', 'raw', False, 'Default value for argument `raw`')
    format =     Option('attachmentnum', 'format', None, 'Default value for argument `format`')

    ### methods for IWikiMacroProvider
    def get_macros(self):
      yield 'AttachmentNum'

    def get_macro_description(self, name):
      return self.__doc__

    def expand_macro(self, formatter, name, content):
        largs, kwargs = parse_args(content)
        try:
            num = int(largs[0]) - 1
            if num < 0:
              raise Exception
        except:
            raise TracError("Argument must be a positive integer!")

        option = self.env.config.get
        if 'raw' in kwargs:
            vraw = kwargs['raw'].lower()
            if vraw in ('yes','true','1','on'):
                raw = True
            elif vraw in ('no','false','0','off'):
                raw = False
        else:
            raw = self.raw

        res  = formatter.resource
        id   = res.id
        type = res.realm

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute( "SELECT filename FROM attachment WHERE type=%s " \
                        "AND id=%s ORDER BY time", (type,id) )

        attmnts = cursor.fetchall()
        if len(attmnts) < num + 1 or not attmnts[num] or not attmnts[num][0]:
            raise TracError("Attachment #%i doesn't exists!" % (num+1))
        filename = attmnts[num][0]

        wikilink = "attachment:'" + filename + "'"
        if raw:
            wikilink = "raw-" + wikilink
        if kwargs.get('format', self.format) == 'short':
            wikilink = "[%s %s]" % (wikilink,filename)
        return format_to_oneliner(self.env, formatter.context, wikilink)

