
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import Formatter
import sys, StringIO, re, traceback, cgi, time
from iface import TracFormDBUser, TracPasswordStoreUser

argRE = re.compile('\s*(".*?"|\'.*?\'|\S+)\s*')
argstrRE = re.compile('%(.*?)%')
tfRE = re.compile('\['
    'tf(?:\.([a-zA-Z_]+?))?'
    '(?::([^\]]*))?'
    '\]')
kwtrans = {
    'class'     : '_class',
    'id'        : '_id',
    }

class TracFormMacro(WikiMacroBase, TracFormDBUser, TracPasswordStoreUser):
    """
    Docs for TracForm macro...
    """

    def expand_macro(self, formatter, name, args):
        processor = TracFormProcessor(self, formatter, name, args)
        return processor.execute()

class TracFormProcessor(object):
    # Default state (beyond what is set in expand_macro).
    showErrors = True
    page = None
    subcontext = None
    default_op = 'checkbox'
    needs_submit = True
    keep_history = False
    track_fields = True
    submit_label = 'Update Form'
    submit_name = None
    form_class = None
    form_cssid = None
    form_name = None

    def __init__(self, macro, formatter, name, args):
        self.macro = macro
        self.formatter = formatter
        self.args = args
        self.name = name

    def execute(self):
        formatter = self.formatter
        args = self.args
        name = self.name

        # Look in the formatter req object for evidence we are executing.
        self.subform = getattr(formatter.req, type(self).__name__, False)
        if not self.subform:
            setattr(formatter.req, type(self).__name__, True)
        self.env = dict(getattr(formatter.req, 'tracform_env', ()))

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
                    kw = {}
                    args = list(self.getargs(line[1:], kw))
                    if len(args):
                        cmd = args.pop(0)
                        fn = getattr(self, 'cmd_' + cmd.lower(), None)
                        if fn is None:
                            errors.append(
                                'ERROR: No TracForm command "%s"' % cmd)
                        else:
                            try:
                                fn(*args, **kw)
                            except Exception, e:
                                errors.append(traceback.format_exc())
            else:
                if self.showErrors:
                    textlines.extend(errors)
                textlines.append(line)
                textlines.extend(srciter)

        # Determine our destination context and load the current state.
        if self.page is None:
            self.page = formatter.req.path_info
        self.context = self.page
        if self.subcontext:
            self.context += ':' + self.subcontext
        state = self.macro.get_tracform_state(self.context)
        self.state = cgi.parse_qs(state or '')
        (self.form_id, self.form_context,
            self.form_updater, self.form_updated_on,
            self.form_keep_history, self.form_track_fields) = \
            self.macro.get_tracform_meta(self.context)

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
        setattr(formatter.req, type(self).__name__, None)

        return ''.join(self.build_form(text))

    def build_form(self, text):
        if not self.subform:
            form_class = self.form_class
            form_cssid = self.form_cssid or self.subcontext
            form_name = self.form_name or self.subcontext
            dest = self.formatter.req.href('/formdata/update')
            yield ('<FORM method="POST" action=%r' % str(dest) + 
                    (form_cssid is not None 
                        and ' id="%s"' % form_cssid
                        or '') +
                    (form_name is not None 
                        and ' name="%s"' % form_name
                        or '') +
                    (form_class is not None 
                        and ' class="%s"' % form_class
                        or '') +
                    '>')
            yield text
            if self.needs_submit:
                yield '<INPUT type="submit"'
                if self.submit_name:
                    yield ' name=%r' % str(self.submit_name)
                yield ' value=%r' % str(self.submit_label)
                yield '>'
            if self.keep_history:
                yield '<INPUT type="hidden"'
                yield ' name="__keep_history__" value="yes">'
            if self.track_fields:
                yield '<INPUT type="hidden"'
                yield ' name="__track_fields__" value="yes">'
            if self.form_updated_on is not None:
                yield '<INPUT type="hidden" name="__basever__"'
                yield ' value="' + str(self.form_updated_on) + '">'
            yield '<INPUT type="hidden" ' + \
                'name="__context__" value=%r>' % str(self.context)
            backpath = self.formatter.req.href(self.formatter.req.path_info)
            yield '<INPUT type="hidden" ' \
                    'name="__backpath__" value=%s>' % str(backpath)
            form_token = self.formatter.req.form_token
            yield '<INPUT type="hidden" ' \
                    'name="__FORM_TOKEN" value=%r>' % str(form_token)
            yield '</FORM>'
        else:
            yield text

    def getargs(self, argstr, kw=None):
        if kw is None:
            kw = {}
        for arg in argRE.findall(argstrRE.sub(self.argsub, argstr) or ''):
            if arg[:1] in '"\'':
                arg = arg[1:-1]
            if arg[:1] == '-':
                name, value = (arg[1:].split('=', 1) + [True])[:2]
                kw[kwtrans.get(name, name)] = value
            else:
                yield arg

    def argsub(self, match):
        name = match.group(1)
        value = self.env.get(name)
        if value is not None:
            return value
        fn = getattr(self, 'env_' + name.lower(), None)
        if fn is not None:
            return fn()
        else:
            return ''

    def env_user(self):
        return self.req.authname

    def env_now(self):
        return time.strftime(time.localtime(time.time()))

    def cmd_errors(self, show):
        self.showErrors = show.upper() in ('SHOW', 'YES')

    def cmd_page(self, page):
        if page.upper() in ('NONE', 'DEFAULT', 'CURRENt'):
            self.page = None
        else:
            self.page = page

    def cmd_subcontext(self, context):
        if context.lower() == 'none':
            self.subcontext = None
        else:
            self.subcontext = str(context)

    def cmd_class(self, value):
        self.form_class = value

    def cmd_id(self, value):
        self.form_cssid = value

    def cmd_name(self, value):
        self.form_name = value

    def cmd_default(self, default):
        self.default_op = default

    def cmd_track_fields(self, track='yes'):
        self.track_fields = track.lower() == 'yes'

    def cmd_keep_history(self, track='yes'):
        self.keep_history = track.lower() == 'yes'

    def cmd_submit_label(self, label):
        self.submit_label = label

    def cmd_submit_name(self, name):
        self.submit_name

    def cmd_setenv(self, name, value):
        self.env[name] = value

    def wiki(self, text):
        out = StringIO.StringIO()
        Formatter(self.formatter.env, self.formatter.context).format(text, out)
        return out.getvalue()

    def process(self, m):
        self.updated = True
        op, argstr = m.groups()
        op = op or self.default_op
        kw = {}
        args = tuple(self.getargs(argstr, kw))
        fn = getattr(self, 'op_' + op.lower(), None)
        if fn is None:
            return 'ERROR: No TracForm operation "%s"' % str(op)
        else:
            try:
                if op[:5] == 'wikiop_':
                    return self.wiki(str(fn(*args)))
                else:
                    return str(fn(*args, **kw))
            except Exception, e:
                return '<PRE>' + traceback.format_exc() + '</PRE>'

    def op_test(self, *args):
        return repr(args)

    def wikiop_value(self, field):
        return 'VALUE=' + field

    def get_field(self, name, default=None, make_single=True):
        current = self.state.get(name, default)
        if make_single and isinstance(current, (tuple, list)):
            if len(current) == 0:
                current = default
            elif len(current) == 1:
                current = current[0]
            else:
                return 'ERROR: field %r has too many values' % str(field)
        return current

    def op_input(self, field, _id=None, _class=None):
        current = self.get_field(field)
        return ("<INPUT name='%s'" % field +
                (_id is not None and ' id="%s"' % _id or '') +
                (_class is not None and ' class="%s"' % _class or '') +
                (current is not None and (" value=%r" % str(current)) or '') +
                '>')

    def op_checkbox(self, field, value=None, _id=None, _class=None):
        current = self.get_field(field)
        if value is not None:
            checked = value == current
        else:
            checked = bool(current)
        return ("<INPUT type='checkbox' name='%s'" % field +
                (_id is not None and ' id="%s"' % _id or '') +
                (_class is not None and ' class="%s"' % _class or '') +
                (value and (' value="' + value + '"') or '') +
                (checked and ' checked' or '') +
                '>')

    def op_radio(self, field, value, _id=None, _class=None):
        current = self.get_field(field)
        return ("<INPUT type='radio' name='%s'" % field +
                (_id is not None and ' id="%s"' % _id or '') +
                (_class is not None and ' class="%s"' % _class or '') +
                " value='%s'" % value +
                (current == value and ' checked' or '') +
                '>')

    def op_select(self, field, *values, **kw):
        _id = kw.pop('_id', None)
        _class = kw.pop('_class', None)
        current = self.get_field(field)
        result = []
        result.append("<SELECT name='%s'" % field +
                (_id is not None and ' id="%s"' % _id or '') +
                (_class is not None and ' class="%s"' % _class or '') +
                '>')
        for value in values:
            value, label = (value.split('//', 1) + [value])[:2]
            result += ("<OPTION value='%s'" % value.strip() +
                    (current == value and ' selected' or '') +
                    '>' + label.strip() + '</OPTION>')
        result.append("</SELECT>")
        return ''.join(result)

    def op_context(self):
        return str(self.context)

    def op_who(self, field):
        who = self.macro.get_tracform_fieldinfo(
            self.context, field)[0] or 'unknown'
        return who
        
    def op_when(self, field, format='%m/%d/%Y %H:%M:%S'):
        when = self.macro.get_tracform_fieldinfo(self.context, field)[1]
        if when is not None:
            when = time.strftime(format, time.localtime(when))
        return when

    def op_id(self):
        return id(self)

    def op_subform(self):
        return self.subform

    def op_form_id(self):
        return self.form_id

    def op_form_context(self):
        return self.form_context

    def op_form_updater(self):
        return self.form_updater

    def op_form_updated_on(self, format='%m/%d/%Y %H:%M:%S'):
        return time.strftime(format, time.localtime(self.form_updated_on))

