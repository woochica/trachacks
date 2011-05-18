# -*- coding: utf-8 -*-

import StringIO
import fnmatch
import re
import time
import traceback

from math import modf

from trac.util.datefmt import format_datetime
from trac.util.text import to_unicode
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import Formatter

from api import FormDBUser, PasswordStoreUser, _
from compat import json
from environment import FormEnvironment
from errors import FormError, FormTooManyValuesError
from util import resource_from_page, xml_escape

argRE = re.compile('\s*(".*?"|\'.*?\'|\S+)\s*')
argstrRE = re.compile('%(.*?)%')
tfRE = re.compile('\['
    'tf(?:\.([a-zA-Z_]+?))?'
    '(?::([^\[\]]*?))?'
    '\]')
kwtrans = {
    'class'     : '_class',
    'id'        : '_id',
    }


class TracFormMacro(WikiMacroBase, FormDBUser, PasswordStoreUser):
    """Docs for TracForms macro..."""

    def expand_macro(self, formatter, name, args):
        processor = FormProcessor(self, formatter, name, args)
        return processor.execute()


class FormProcessor(object):
    """Core parser and processor logic for TracForms markup."""

    # Default state (beyond what is set in expand_macro).
    showErrors = True
    page = None
    subcontext = None
    default_op = 'checkbox'
    allow_submit = False
    keep_history = False
    track_fields = True
    submit_label = None
    submit_name = None
    form_class = None
    form_cssid = None
    form_name = None
    sorted_env = None

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

        # Setup preliminary context
        self.page = formatter.req.path_info
        if self.page == '/wiki' or self.page == '/wiki/':
            self.page = '/wiki/WikiStart'
        realm, resource_id = resource_from_page(formatter.env, self.page)

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
                                _("ERROR: No TracForms command '%s'" % cmd))
                        else:
                            try:
                                fn(*args, **kw)
                            except FormError, e:
                                errors.append(str(e))
                            except Exception, e:
                                errors.append(traceback.format_exc())
            else:
                if self.showErrors:
                    textlines.extend(errors)
                textlines.append(line)
                textlines.extend(srciter)

        # Determine our destination context and load the current state.
        self.context = tuple([realm, resource_id,
                              self.subcontext is not None and \
                              self.subcontext or ''])
        state = self.macro.get_tracform_state(self.context)
        self.formatter.env.log.debug(
            'TracForms state = ' + (state is not None and state or ''))
        for name, value in json.loads(state or '{}').iteritems():
            self.env[name] = value
            self.formatter.env.log.debug(
                name + ' = ' + to_unicode(value))
            if self.subcontext is not None:
                self.env[self.subcontext + ':' + name] = value
        self.sorted_env = None
        (self.form_id, self.form_realm, self.form_resource_id,
            self.form_subcontext, self.form_updater, self.form_updated_on,
            self.form_keep_history, self.form_track_fields) = \
            self.macro.get_tracform_meta(self.context)
        self.form_id = self.form_id is not None and int(self.form_id) or None

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

        self.formatter.env.log.debug('TracForms parsing finished')
        if 'FORM_EDIT_VAL' in formatter.perm:
            self.allow_submit = True
        return ''.join(self.build_form(text))

    def build_form(self, text):
        if not self.subform:
            form_class = self.form_class
            form_cssid = self.form_cssid or self.subcontext
            form_name = self.form_name or self.subcontext
            dest = self.formatter.req.href('/form/update')
            yield ('<FORM class="printableform" ' +
                    'method="POST" action=%r' % str(dest) +
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
            if self.allow_submit:
                # TRANSLATOR: Default submit button label
                submit_label = self.submit_label or _("Update Form")
                yield '<INPUT class="buttons" type="submit"'
                if self.submit_name:
                    yield ' name=%r' % str(self.submit_name)
                yield ' value=%r' % xml_escape(submit_label)
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
            context = json.dumps(
                self.context, separators=(',', ':'))
            yield '<INPUT type="hidden" ' + \
                'name="__context__" value=%r>' % context
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
                try:
                    arg = (str(float(arg)))
                    yield arg
                except ValueError, e:
                    name, value = (arg[1:].split('=', 1) + [True])[:2]
                    kw[str(kwtrans.get(name, name))] = value
                    pass
            else:
                yield arg

    def argsub(self, match, NOT_FOUND=KeyError, aslist=False):
        if isinstance(match, basestring):
            name = match
        else:
            name = match.group(1)
        if name[:1] in '"\'':
            quote = True
            name = name[1:-1]
        else:
            quote = False
        if '*' in name or '?' in name or '[' in name:
            value = []
            keys = self.get_sorted_env()
            for key in fnmatch.filter(keys, name):
                obj = self.env[key]
                if isinstance(obj, (tuple, list)):
                    value.extend(obj)
                else:
                    value.append(obj)
            if not value and self.page:
                for key in fnmatch.filter(keys, self.page + ':' + name):
                    obj = self.env[key]
                    if isinstance(obj, (tuple, list)):
                        value.extend(obj)
                    else:
                        value.append(obj)
            if not value and self.subcontext:
                for key in fnmatch.filter(keys, self.subcontext + ':' + name):
                    obj = self.env[key]
                    if isinstance(obj, (tuple, list)):
                        value.extend(obj)
                    else:
                        value.append(obj)
            if not value:
                for key in fnmatch.filter(keys, name):
                    obj = self.env[key]
                    if isinstance(obj, (tuple, list)):
                        value.extend(obj)
                    else:
                        value.append(obj)
        else:
            value = self.env.get(name, NOT_FOUND)
            if self.page is not None and value is NOT_FOUND:
                value = self.env.get(self.page + ':' + name, NOT_FOUND)
            if self.subcontext is not None and value is NOT_FOUND:
                value = self.env.get(self.subcontext + ':' + name, NOT_FOUND)
            if value is NOT_FOUND:
                value = self.env.get(name, NOT_FOUND)
            if value is NOT_FOUND:
                fn = getattr(self, 'env:' + name.lower(), None)
                if fn is not None:
                    value = fn()
                else:
                    value = ''
        if aslist:
            if isinstance(value, (list, tuple)):
                return tuple(value)
            else:
                return (value,)
        else:
            if isinstance(value, (list, tuple)):
                return ' '.join(
                    quote and repr(str(item)) or str(item) for item in value)
            else:
                value = str(value)
                if quote:
                    value = repr(value)
                return value

    def get_sorted_env(self):
        if self.sorted_env is None:
            self.sorted_env = sorted(self.env)
        return self.sorted_env

    def env_user(self):
        return self.req.authname

    def env_now(self):
        return time.strftime(time.localtime(time.time()))

    def cmd_errors(self, show):
        self.showErrors = show.upper() in ('SHOW', 'TRUE', 'YES')

    def cmd_page(self, page):
        if page.upper() in ('NONE', 'DEFAULT', 'CURRENT'):
            self.page = None
        else:
            self.page = page

    def cmd_subcontext(self, context):
        if context.lower() == 'none':
            self.subcontext = None
        else:
            self.subcontext = str(context)

    def cmd_load(self, subcontext, page=None):
        if page is None:
            page = self.page
        context = page + ':' + subcontext
        state = self.macro.get_tracform_state(context)
        for name, value in json.loads(state or '{}').iteritems():
            self.env[context + ':' + name] = value
            if self.subcontext is not None:
                self.env[self.subcontext + ':' + name] = value

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
        self.sorted_env = None

    def cmd_setlist(self, name, *values):
        self.env[name] = tuple(values)
        self.sorted_env = None

    def cmd_operation(_self, _name, _op, *_args, **_kw):
        if _op in ('is', 'as'):
            _op, _args = _args[0], _args[1:]
        op = getattr(_self, 'op_' + _op, None)
        if op is None:
            raise FormTooManyValuesError(str(_name))
        def partial(*_newargs, **_newkw):
            if _kw or _newkw:
                kw = dict(_kw)
                kw.update(_newkw)
            else:
                kw = {}
            return op(*(_newargs + _args), **kw)
        _self.env['op:' + _name] = partial

    def wiki(self, text):
        out = StringIO.StringIO()
        Formatter(self.formatter.env, self.formatter.context).format(text, out)
        return out.getvalue()

    def process(self, m):
        self.updated = True
        op, argstr = m.groups()
        op = op or self.default_op
        self.formatter.env.log.debug('Converting TracForms op: ' + str(op))
        kw = {}
        args = tuple(self.getargs(argstr, kw))
        fn = self.env.get('op:' + op.lower())
        if fn is None:
            fn = getattr(self, 'op_' + op.lower(), None)
        if fn is None:
            raise FormTooManyValuesError(str(op))
        else:
            try:
                if op[:5] == 'wikiop_':
                    self.formatter.env.log.debug(
                        'TracForms wiki value: ' + self.wiki(str(fn(*args))))
                    return self.wiki(str(fn(*args)))
                else:
                    self.formatter.env.log.debug(
                        'TracForms value: ' + to_unicode(fn(*args, **kw)))
                    return to_unicode(fn(*args, **kw))
            except FormError, e:
                return '<PRE>' + str(e) + '</PRE>'
            except Exception, e:
                return '<PRE>' + traceback.format_exc() + '</PRE>'

    def op_test(self, *args):
        return repr(args)

    def wikiop_value(self, field):
        return 'VALUE=' + field

    def get_field(self, name, default=None, make_single=True):
        current = self.env.get(name, default)
        if make_single and isinstance(current, (tuple, list)):
            if len(current) == 0:
                current = default
            elif len(current) == 1:
                current = current[0]
            else:
                raise FormTooManyValuesError(str(name))
        return current

    def op_input(self, field, content=None, size=None, _id=None, _class=None):
        current = self.get_field(field)
        if current is not None:
            content = current
        return ("<INPUT name='%s'" % field +
                (size is not None and ' size="%s"' % size or '') +
                (_id is not None and ' id="%s"' % _id or '') +
                (_class is not None and ' class="%s"' % _class or '') +
                (content is not None and (" value=%r" % xml_escape(
                                                     content)) or '') +
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

    def op_textarea(self, field, content='',
                    cols=None, rows=None,
                    _id=None, _class=None):
        current = self.get_field(field)
        if current is not None:
            content = current
        return ("<TEXTAREA name='%s'" % field +
                (cols is not None and ' cols="%s"' % cols or '') +
                (rows is not None and ' rows="%s"' % rows or '') +
                (_id is not None and ' id="%s"' % _id or '') +
                (_class is not None and ' class="%s"' % _class or '') +
                '>' + content + '</TEXTAREA>')

    def op_context(self):
        return str(self.context)

    def op_who(self, field):
        # TRANSLATOR: Default updater name
        who = self.macro.get_tracform_fieldinfo(
                self.context, field)[0] or _("unknown")
        return who
        
    def op_when(self, field, format='%m/%d/%Y %H:%M:%S'):
        when = self.macro.get_tracform_fieldinfo(self.context, field)[1]
        return (when is not None and format_datetime(
                when, format=str(format)) or _("unknown"))

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

    def op_sum(self, *values):
        """Full precision summation using multiple floats for intermediate
           values
        """
        ## msum() from http://code.activestate.com/recipes/393090/ (r5)
        # Depends on IEEE-754 arithmetic guarantees.
        partials = []               # sorted, non-overlapping partial sums
        for x in values:
            x = float(x)
            i = 0
            for y in partials:
                if abs(x) < abs(y):
                    x, y = y, x
                hi = x + y
                lo = y - (hi - x)
                if lo:
                    partials[i] = lo
                    i += 1
                x = hi
            partials[i:] = [x]
        result = sum(partials, 0.0)
        # finally reduce display precision to integer, if possible
        if modf(result)[0] == 0:
            return str(int(result))
        return str(result)

    def op_sumif(self, check, *values):
        return self.op_sum(*self.filter(check, values))

    def op_count(self, *values):
        return str(len(values))

    def op_countif(self, check, *values):
        return self.op_count(*self.filter(check, values))

    def op_filter(self, check, *values):
        return ' '.join(str(item) for item in self.filter(check, values))

    def filter(self, check, values):
        if check[:1] == '/' and check[-1:] == '/':
            return re.findall(check[1: -1], values)
        elif '*' in check or '?' in check or '[' in check:
            return fnmatch.filter(values, check)
        else:
            return [i for i in values if check == i]

    def op_sumprod(self, *values, **kw):
        stride = int(kw.pop('stride', 2))
        total = 0
        irange = range(stride)
        for index in xrange(0, len(values), stride):
            row = 1.0
            for inner in irange:
                row *= float(values[inner + index])
            total += row
        return str(total)

    def op_int(self, *values):
        return ' '.join(str(int(float(value))) for value in values)

    def op_value(self, *names):
        return ' '.join(self.argsub(name) for name in names)

    def op_quote(self, *names):
        return ' '.join(repr(self.argsub(name)) for name in names)

    def op_zip(self, *names):
        zipped = zip(*(self.argsub(name, aslist=True) for name in names))
        return ' '.join(' '.join(str(item) for item in level)
                        for level in zipped)

    def op_env_debug(self, pattern='*'):
        result = []
        for key in fnmatch.filter(self.get_sorted_env(), pattern):
            result.append('%s = %s<BR>' % (key, self.env[key]))
        return ''.join(result)

