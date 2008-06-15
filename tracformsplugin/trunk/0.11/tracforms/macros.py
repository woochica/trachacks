
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import Formatter
import sys, StringIO, re, traceback

argRE = re.compile('\s*(".*?"|\'.*?\'|\S+)\s*')
tfRE = re.compile('\['
    'tf(?:\.([a-zA-Z_]+?))?'
    '(?::(.*))?'
    '\]')

class TracFormMacro(WikiMacroBase):
    """
    Docs for TracForm macro...
    """

    # Default state (beyond what is set in expand_macro).
    showErrors = True
    page = None

    def expand_macro(self, formatter, name, args):
        self.formatter = formatter
        self.name = name
        self.args = args
        try:
            # Remove leading comments and process commands.
            textlines = []
            errors = []
            srciter = iter(args.split('\n'))
            for line in srciter:
                if line[:1] == '#':
                    # Comment or operation.
                    line = line.strip()[1:]
                    if line[:1] == '!':
                        # It's a command, parse the arguments...
                        args = tuple(self.getargs(line[1:]))
                        cmd = args.pop(0)
                        fn = getattr(self, 'cmd_' + cmd.lower(), None)
                        if fn is None:
                            errors.append(
                                'ERROR: No TracForm command "%s"' % cmd)
                        else:
                            try:
                                fn(*args)
                            except Exception, e:
                                errors.append(traceback.format_exc())
                else:
                    if self.showErrors:
                        textlines.extend(errors)
                    textlines.append(line)
                    textlines.extend(srciter)

            # Determine our destination context.
            if self.page is None:
                self.page = formatter.req.path_info

            # Wiki-ize the text, this will allow other macros to execute after
            # which we can do our own replacements within whatever formatted
            # junk is left over.
            text = self.wiki('\n'.join(textlines))

            # Keep replacing tf: sections until there are no more
            # replacements.  On each substitution, wiki() is called on the
            # result.
            self.updated = True
            while self.updated:
                self.updated = False
                text = tfRE.sub(self.process, text)
            return text
        finally:
            self.fomratter = None
            self.name = None
            self.args = None

    @staticmethod
    def getargs(argstr):
        for arg in argRE.findall(argstr):
            if arg[:1] in '"\'':
                yield arg[1:-1]
            else:
                yield arg

    def cmd_errors(self, show):
        self.showErrors = show.upper() in ('SHOW', 'YES')

    def cmd_page(self, page):
        if page.upper() in ('NONE', 'DEFAULT', 'CURRENt'):
            self.page = None
        else:
            self.page = page

    def wiki(self, text):
        out = StringIO.StringIO()
        Formatter(self.formatter.env, self.formatter.context).format(text, out)
        return out.getvalue()

    def process(self, m):
        self.updated = True
        op, argstr = m.groups()
        op = op or 'value'
        args = tuple(self.getargs(argstr))
        fn = getattr(self, 'op_' + op.lower(), None)
        if fn is None:
            return 'ERROR: No TracForm operation "%s"' % str(op)
        else:
            try:
                return self.wiki(fn(*args))
            except Exception, e:
                return self.wiki(traceback.format_exc())

    def op_test(self, *args):
        return repr(args)

    def op_value(self, field):
        return 'VALUE=' + field

