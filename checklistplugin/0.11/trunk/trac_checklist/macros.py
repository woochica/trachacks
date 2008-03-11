#
#   macros.py -- Guts that support the wiki-zation of checklists.
#

from genshi.builder import tag

from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import Formatter, extract_link
from trac.util.html import Markup
from trac.core import ExtensionPoint

from db import IChecklistDBObserver

import re, StringIO, cgi

checklistRE = re.compile('\[cl:(.*?)\{(.*?)\}\]', re.M | re.S)

class ChecklistMacro(WikiMacroBase):
    clobservers = ExtensionPoint(IChecklistDBObserver)

    def expand_macro(self, formatter, name, args):
        lines = iter(args.split('\n'))
        flags = {}
        for line in lines:
            line = line.strip()
            if line[:1] == '#':
                continue
            elif line[:1] == '-':
                name, value = (line[1:].split('=', 1) + [True])[:2]
                flags[name.strip()] = \
                    isinstance(value, basestring) and value.strip() or value
            else:
                break
        text = '\n'.join(lines)
        context = flags.get('context', formatter.req.path_info)
        # There MUST be an easier way...
        link = extract_link(formatter.env, formatter.context, context)
        if link is not None:
            for op in link.generate():
                self.log.debug('HERE >>>>>>>>>>>>>> ', str(op))
                if isinstance(op, tuple):
                    if op[0] == 'a':
                        for name, value in op[1]:
                            if name == 'href':
                                context = value
                                break
        section = flags.get('section')
        can_set = str(flags.get('can-set', ''))
        can_get = str(flags.get('can-get', ''))
        can_change = str(flags.get('can-change', ''))
        if section:
            context += '::' + section
        data = self.fetchContext(context)
        notes = dict(
            name=(section or 'Checklist')
            )

        def replacer(match):
            op, field = match.groups()
            op, argstr = (op.split(':', 1) + [''])[:2]
            fn = getattr(self,
                'op_' + (op or 'checkbox').replace('-', '_'), None)
            if fn is not None:
                args = [arg.strip() for arg in argstr.split(':')]
                return fn(field, data, notes, *(arg for arg in args if arg))
            else:
                return 'ERROR: No function for operation %r' % op

        # Replace cl fields.
        html = ''.join(checklistRE.sub(replacer, self.wikize(formatter, text)))

        href = formatter.req.href('checklist/update')
        return ''.join((
            '<FORM method="GET" action="%s"' % href,
                '>',
            '<INPUT type="hidden" name="can-set:*" value=%r>' % can_set,
            '<INPUT type="hidden" name="can-get:*" value=%r>' % can_get,
            '<INPUT type="hidden" name="can-change:*" value=%r>' % can_change,
            '<INPUT type="hidden" name="__backpath__" value=%r>' 
                % formatter.req.href(formatter.req.path_info),
            '<INPUT type="hidden" name="__context__" value=%r>' % str(context),
            html,
            not notes.get('submit') and self.op_submit(None, data, notes) or '',
            '</FORM>',
            ))

    def wikize(self, formatter, text):
        out = StringIO.StringIO()
        Formatter(formatter.env, formatter.context).format(text, out)
        return out.getvalue()

    def fetchContext(self, context):
        for observer in self.clobservers:
            result = observer.checklist_getValues(context)
            if result is not None:
                return result

    def op_checkbox(self, field, data, notes):
        checked = data.get(field, (False, None, None))[0]
        return ''.join((
            '<INPUT type="hidden" name="__fields__" value=%r>' % str(field),
            '<INPUT type="hidden" name=%r value=%r>' %
                ('old:' + str(field), checked and 'on' or ''),
            '<INPUT type="checkbox" name=%r' % str(field),
                checked and ' checked' or '',
                '>',
            ))

    def op_who(self, field, data, notes):
        return cgi.escape(data.get(field, (False, None, '<noone>'))[2])

    def op_when(self, field, data, notes):
        return cgi.escape(
            str(data.get(field, (False, '<unknown>', None))[1])[:19])

    def op_submit(self, field, data, notes):
        notes['submit'] = True
        field = str(field or 'Update ' + notes['name'])
        return ''.join((
            '<INPUT type="submit" value=%r>' % field
            ))

    def op_can_set(self, field, data, notes, right=''):
        return ''.join((
            '<INPUT type="hidden" name=%r value=%r>' %
                ('can-set:' + field, right)
            ))

    def op_can_get(self, field, data, notes, right=''):
        return ''.join((
            '<INPUT type="hidden" name=%r value=%r>' %
                ('can-get:' + field, right)
            ))

    def op_can_change(self, field, data, notes, right=''):
        return ''.join((
            '<INPUT type="hidden" name=%r value=%r>' %
                ('can-change:' + field, right)
            ))

