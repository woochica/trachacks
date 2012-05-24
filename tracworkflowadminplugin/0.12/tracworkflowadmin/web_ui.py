# -*- coding:utf-8 -*-

import ConfigParser
import glob
import os
import re
import time
from cStringIO import StringIO
from pkg_resources import resource_filename
from subprocess import Popen, PIPE
from tempfile import mkstemp
try:
    import json
except ImportError:
    import simplejson as json

from trac.core import Component, implements
from trac.admin import IAdminPanelProvider
from trac.config import Configuration, Option, BoolOption, ListOption, \
                        FloatOption, ChoiceOption
from trac.env import IEnvironmentSetupParticipant
from trac.perm import PermissionSystem
from trac.util.compat import md5
from trac.util.text import to_unicode, exception_to_unicode
from trac.util.translation import dgettext, domain_functions
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script, \
                            add_script_data


_, add_domain = domain_functions('tracworkflowadmin', '_', 'add_domain')

__all__ = ['TracWorkflowAdminModule']


def _msgjs_locales(dir=None):
    if dir is None:
        dir = resource_filename(__name__, 'htdocs')
        dir = os.path.join(dir, 'scripts', 'messages')
    if not os.path.isdir(dir):
        return set()
    return set(file[0:-3] for file in os.listdir(dir) if file.endswith('.js'))


class TracWorkflowAdminModule(Component):
    implements(IAdminPanelProvider, ITemplateProvider,
               IEnvironmentSetupParticipant)

    operations = ListOption('workflow-admin', 'operations',
        'del_owner,set_owner,set_owner_to_self,del_resolution,set_resolution,leave_status',
        doc="Operations in workflow admin")
    dot_path = Option('workflow-admin', 'dot_path', 'dot',
        doc="Path to the dot executable")
    diagram_cache = BoolOption('workflow-admin', 'diagram_cache', 'false',
        doc="Enable cache of workflow diagram image")
    diagram_size = Option('workflow-admin', 'diagram_size', '6, 6',
        doc="Image size in workflow diagram")
    diagram_font = Option('workflow-admin', 'diagram_font', 'sans-serif',
        doc="Font name in workflow diagram")
    diagram_fontsize = FloatOption('workflow-admin', 'diagram_fontsize', '10',
        doc="Font size in workflow diagram")
    diagram_colors = ListOption('workflow-admin', 'diagram_colors',
        '#0000ff,#006600,#ff0000,#666600,#ff00ff',
        doc="Colors of arrows in workflow diagram")
    default_editor = ChoiceOption(
        'workflow-admin', 'default_editor', ['gui', 'text'],
        doc="Default mode of the workflow editor")
    auto_update_interval = Option('workflow-admin', 'auto_update_interval', '3000',
        doc="""An automatic-updating interval for text mode is specified by a
        milli second bit. It is not performed when 0 is specified.""")

    msgjs_locales = _msgjs_locales()
    _action_name_re = re.compile(r'\A[A-Za-z0-9_-]+\Z')
    _number_re = re.compile(r'\A[0-9]+\Z')
    _editor_mode = 'gui'

    def __init__(self):
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

    # IEnvironmentSetupParticipant
    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        return False

    def upgrade_environment(self, db):
        pass

    # ITemplateProvider method
    def get_htdocs_dirs(self):
        return [('tracworkflowadmin', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield ('ticket', dgettext("messages", ("Ticket System")),
                   'workflowadmin', _("Workflow Admin"))

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('TRAC_ADMIN')
        if req.method == 'POST':
            self._parse_request(req)

        action, status = self._conf_to_inner_format(self.config)
        operations = self.operations
        permissions = self._get_permissions(req)
        add_stylesheet(req, 'tracworkflowadmin/themes/base/jquery-ui.css')
        add_stylesheet(req, 'tracworkflowadmin/css/tracworkflowadmin.css')
        add_stylesheet(req, 'tracworkflowadmin/css/jquery.multiselect.css')
        add_script(req, 'tracworkflowadmin/scripts/jquery-ui.js')
        add_script(req, 'tracworkflowadmin/scripts/jquery.json-2.2.js')
        add_script(req, 'tracworkflowadmin/scripts/jquery.multiselect.js')
        add_script(req, 'tracworkflowadmin/scripts/main.js')
        add_script_data(req, {'auto_update_interval': int(self.auto_update_interval)})
        if req.locale and str(req.locale) in self.msgjs_locales:
            add_script(req, 'tracworkflowadmin/scripts/messages/%s.js' % req.locale)
        data = {
            'actions': action,
            'status': status,
            'perms': permissions,
            'operations': operations,
            'editor_mode': req.args.get('editor_mode') or self.default_editor,
            'text': self._conf_to_str(self.config)
        }
        return 'tracworkflowadmin.html', data

    def _conf_to_inner_format(self, conf):
        statuses = []
        for name, value in conf.options('ticket-workflow'):
            if name.endswith('.operations') and 'leave_status' in [before.strip() for before in value.split(',')]:
                values = conf.get('ticket-workflow', name[0:-11]).split('->')
                if values[1].strip() == '*':
                    for name in values[0].split(','):
                        st = name.strip()
                        if st != '*':
                            statuses.append(st)
                    break
        actions = {}

        count = 1
        for name, value in conf.options('ticket-workflow'):
            param = name.split('.')
            actionName = param[0].strip()
            regValue = ''
            if len(param) == 1:
                pieces = [val.strip() for val in value.split('->')]
                before = pieces[0]
                next = '*'
                if len(pieces) > 1:
                    next = pieces[1]
                regValue = {'next': next, 'before': {}}
                if next != '*' and next not in statuses:
                        statuses.append(next)
                if before != '*':
                    for val in before.split(','):
                        tmp = val.strip()
                        if tmp != '':
                            regValue['before'][tmp] = 1
                            if tmp != '*' and tmp not in statuses:
                                statuses.append(tmp)
                else:
                    regValue['before'] = '*'
                if not actions.has_key(actionName):
                    actions[actionName] = {'tempName': actionName, 'lineInfo': {}}
                actions[actionName]['next'] = regValue['next']
                actions[actionName]['before'] = regValue['before']
            else:
                regKey = param[1].strip()
                if regKey == 'permissions' or regKey == 'operations':
                    tmp = []
                    for v in value.strip().split(','):
                        tmp2 = v.strip()
                        if  tmp2 != '':
                            tmp.append(v.strip())
                    regValue = tmp
                else:
                    regValue = value.strip()
                if not actions.has_key(actionName):
                    actions[actionName] = {'tempName': actionName, 'lineInfo': {}}
                actions[actionName][regKey] = regValue
            count = count + 1

        action_elements = []
        for key in actions:
            tmp = actions[key]
            tmp['action'] = key
            if not tmp.has_key('default'):
                tmp['default'] = 0
            elif not self._number_re.match(tmp['default']):
                tmp['default'] = -1
            if not tmp.has_key('permissions'):
                tmp['permissions'] = ['All Users']
            if not tmp.has_key('name'):
                tmp['name'] = ''
            if tmp.has_key('before') and tmp['before'] == '*':
                tmp['before'] = {}
                for st in statuses:
                    tmp['before'][st] = 1
            action_elements.append(tmp)
        action_elements.sort(key=lambda v: int(v['default']), reverse=True)
        return (action_elements, statuses)

    def _conf_to_str(self, conf):
        tmp = ConfigParser.ConfigParser()
        tmp.add_section('ticket-workflow')
        for name, value in conf.options('ticket-workflow'):
            tmp.set('ticket-workflow', name.encode('utf-8'), value.encode('utf-8'))

        f = StringIO()
        tmp.write(f)
        f.flush()
        f.seek(0)
        lines = [line.decode('utf-8') for line in f
                                      if not line.startswith('[')]
        lines.sort()
        return ''.join(lines)

    def _str_to_inner_format(self, str, out):
        lines = str.splitlines(False)
        errors = []
        lineInfo = {}
        firstLineInfo = {}  # dict of (action, lineno)
        others = {}
        for idx, line in enumerate(lines):
            lineno = idx + 1
            line = line.strip()
            lines[idx] = line
            if not line or line.startswith('#') or line.startswith(';'):
                continue
            if line.startswith('['):
                errors.append(_("Line %(num)d: Could not use section.",
                                num=lineno))
                continue
            if '=' not in line:
                errors.append(_(
                    "Line %(num)d: This line is not pair of key and value.",
                    num=lineno))
                continue
            key, value = line.split('=', 1)
            key = key.strip().lower()
            value = value.strip()
            if key in lineInfo:
                errors.append(_(
                    "Line %(num)d: There is a same key in line %(num2)d.",
                    num=lineno, num2=lineInfo[key]))
                continue
            lineInfo[key] = lineno
            keys = key.split('.', 1)
            firstLineInfo.setdefault(keys[0], lineno)
            if len(keys) == 1:
                if '->' not in value:
                    errors.append(_(
                        "Line %(num)d: Must be \"<action> = <status-list> -> "
                        "<new-status>\" format.", num=lineno))
                    continue
                stats = [stat.strip()
                         for stat in value.split('->')[0].split(',')]
                for n, stat in enumerate(stats):
                    if not stat:
                        errors.append(_(
                            "Line %(num)d: #%(n)d status is empty.",
                            num=lineno, n=n + 1))
            else:
                attr = keys[1]
                if '.' in attr:
                    errors.append(_(
                        "Line %(num)d: Must be \"<action>.<attribute> = "
                        "<value>\" format.", num=lineno))
                    continue
                if attr not in ('default', 'name', 'operations', 'permissions'):
                    others.setdefault(keys[0], {})
                    others[keys[0]][attr] = value

        if not firstLineInfo:
            errors.append(_("There is no valid description."))

        actions = sorted(firstLineInfo.iterkeys())
        for key in actions:
            if key not in lineInfo:
                errors.append(_(
                    "Line %(num)d: Require \"%(action)s = <status-list> -> "
                    "<new-status>\" line.",
                    num=firstLineInfo[key], action=key))

        if len(errors) != 0:
            out['textError'] = errors;
            return

        contents = '\n'.join(['[ticket-workflow]'] + lines).encode('utf-8')
        tmp_fd, tmp_file = mkstemp('.ini', 'workflow-admin')
        try:
            tmp_fp = os.fdopen(tmp_fd, 'w')
            tmp_fd = None
            try:
                tmp_fp.write(contents)
            finally:
                tmp_fp.close()
            tmp_conf = Configuration(tmp_file)
        finally:
            if tmp_fd is not None:
                os.close(tmp_fd)
            os.remove(tmp_file)

        try:
            out['actions'], out['status'] = self._conf_to_inner_format(tmp_conf)
        except ConfigParser.Error, e:
            out['textError'] = [to_unicode(e)]
            return
        out['lineInfo'] = lineInfo
        out['firstLineInfo'] = firstLineInfo
        out['others'] = others

    def _json_to_inner_format(self, out):
        out['lineInfo'] = {}
        out['firstLineInfo'] = {}
        out['others'] = {}
        if 'actions' in out:
            count = 1
            for act in out['actions']:
                act['tempName'] = act['action']
                out['firstLineInfo'][act['action']] = count
                for subparam in ['', '.default', '.name', '.operations', '.permissions']:
                    out['lineInfo'][act['action'] + subparam] = count
                count = count + 1

    def _get_permissions(self, req):
        actions = ['All Users']
        actions.extend(sorted(
            PermissionSystem(self.env).get_actions(),
            key=lambda act: (not act.startswith('TICKET_'), act)))
        return actions

    def _create_dot_script(self, params):
        def dot_escape(text):
            return text.replace('\\', '\\\\').replace('"', '\\"')

        script = u'digraph workflow {\n'
        size = self.diagram_size.split(',')
        colors = self.diagram_colors

        script += ' size="%g, %g";\n' % (float(size[0]), float(size[1]))
        node_attrs = ['style=rounded', 'shape=box',
                      'fontsize="%g"' % self.diagram_fontsize]
        if self.diagram_font:
            node_attrs.append('fontname="%s"' % dot_escape(self.diagram_font))
        script += ' node [%s];\n' % ', '.join(node_attrs)
        statusRev = {}
        for idx, stat in enumerate(params['status']):
            script +=  ' node_%d [label="%s"]' % (idx, dot_escape(stat))
            script +=  " {rank = same; node_%d}\n" % idx
            statusRev[stat] = idx
        script += "\n"
        count = 0
        for action in params['actions']:
            next = action['next'].strip()
            if next == '*':
                continue
            edgeParams = []
            name = action['name'].strip()
            if name == '':
                name = action['tempName']
            edgeParams.append('label="%s"' % dot_escape(name))
            if self.diagram_font:
                edgeParams.append('fontname="%s"' % dot_escape(self.diagram_font))
            edgeParams.append('fontsize="%g"' % self.diagram_fontsize)
            color = colors[count % len(colors)]
            edgeParams.append('color="%s"' % dot_escape(color))
            edgeParams.append('fontcolor="%s"' % dot_escape(color))
            for before in action['before']:
                edgeParams2 = edgeParams[:]
                if before in statusRev and next in statusRev:
                    if statusRev[next] - statusRev[before] == 1:
                        edgeParams2.append('weight=50')
                    script += " node_%d -> node_%d [" % (statusRev[before], statusRev[next])
                    script += ','.join(edgeParams2)
                    script += '];\n'
            count += 1
        script += '}\n'

        return script.encode('utf-8')

    def _image_path_setup(self, req):
        dir = os.path.join(self.env.get_htdocs_dir(), 'tracworkflowadmin')
        if not os.path.isdir(dir):
            os.mkdir(dir)
        for file in glob.glob(os.path.join(dir, '*')):
            try:
                if os.stat(file).st_mtime + 60 * 60 * 24 < time.time():
                    os.unlink(file)
            except:
                pass

    def _image_tmp_path(self, basename):
        return os.path.join(self.env.get_htdocs_dir(), 'tracworkflowadmin', basename)

    def _image_tmp_url(self, req, basename):
        return req.href.chrome('site/tracworkflowadmin/%s' % basename)

    def _update_diagram(self, req, params):
        _, errors = self._validate_workflow(req, params)
        basename = 'error.png'
        if len(errors) == 0:
            script = self._create_dot_script(params)
            self._image_path_setup(req)
            dir = os.path.join(self.env.get_htdocs_dir(), 'tracworkflowadmin')
            basename = '%s.png' % md5(script).hexdigest()
            path = os.path.join(dir, basename)
            if self.diagram_cache and os.path.isfile(path):
                os.utime(path, None)
            else:
                self._create_diagram_image(path, dir, script, errors)
        data = {'result': (1, 0)[len(errors) == 0],     # 0 if cond else 1
                'errors': errors,
                'image_url': self._image_tmp_url(req, basename)}
        req.send(json.dumps(data))
        # NOTREACHED

    def _create_diagram_image(self, path, dir, script, errors):
        fd, tmp = mkstemp(suffix='.png', dir=dir)
        os.close(fd)
        try:
            try:
                proc = Popen([self.dot_path, '-Tpng', '-o', tmp], stdin=PIPE)
            except OSError, e:
                errors.append(_(
                    "The dot command '%(path)s' is not available: %(e)s",
                    path=self.dot_path, e=exception_to_unicode(e)))
                os.remove(tmp)
                return
            try:
                proc.stdin.write(script)
            finally:
                proc.stdin.close()
                proc.wait()
        except:
            os.remove(tmp)
            raise
        else:
            try:
                os.remove(path)
            except:
                pass
            os.rename(tmp, path)

    def _get_init_workflow(self):
        config = {
            'leave': 'new,assigned,accepted,reopened,closed -> *',
            'leave.default': '9',
            'leave.name': _("Leave"),
            'leave.operations': 'leave_status',
            'accept': 'new,assigned,accepted,reopened -> accepted',
            'accept.default': '7',
            'accept.name': _("Accept"),
            'accept.operations': 'set_owner_to_self',
            'accept.permissions': 'TICKET_MODIFY',
            'reassign': 'new,assigned,accepted,reopened -> assigned',
            'reassign.default': '5',
            'reassign.name': _("Reassign"),
            'reassign.operations': 'set_owner',
            'reassign.permissions': 'TICKET_MODIFY',
            'reopen': 'closed -> reopened',
            'reopen.default': '3',
            'reopen.name': _("Reopen"),
            'reopen.operations': 'del_resolution',
            'reopen.permissions': 'TICKET_CREATE',
            'resolve': 'new,assigned,accepted,reopened -> closed',
            'resolve.default': '1',
            'resolve.name': _("Resolve"),
            'resolve.operations': 'set_resolution',
            'resolve.permissions': 'TICKET_MODIFY',
        }
        return config.iteritems()

    def _initialize_workflow(self, req):
        for (name, value) in self.config.options('ticket-workflow'):
            self.config.remove('ticket-workflow', name)

        has_init = False
        for (name, value) in self.config.options('workflow-admin-init'):
            self.config.set('ticket-workflow', name, value)
            has_init = True
        if not has_init:
            for (name, value) in self._get_init_workflow():
                self.config.set('ticket-workflow', name, value)

        self.config.save()

    def _validate_workflow(self, req, params):

        if 'textError' in params:
            return {}, params['textError']

        errors = []
        if not 'actions' in params:
            errors.append(_("Invalid request without actions. Please restart "
                            "your browser and retry."))
        if len(params['actions']) == 0:
            errors.append(_("Need at least one action."))
        if not 'status' in params:
            errors.append(_("Invalid request without statuses. Please restart "
                            "your browser and retry."))
        if len(params['status']) == 0:
            errors.append(_("Need at least one status."))

        newOptions = {}

        if len(errors) == 0:
            leave_status_exists = False
            for act in params['actions']:
                if 'leave_status' in act['operations'] and act['next'] == '*':
                    leave_status_exists = True
                    break
            if not leave_status_exists:
                errors.append(_("The action with operation 'leave_status' and "
                                "next status '*' is certainly required."))

        if len(errors) == 0:
            lineInfo = params['lineInfo']
            perms = self._get_permissions(req)
            perms.append('All Users')
            operations = self.operations
            actionNames = []
            for act in params['actions']:
                lineErrors = []
                tempName = act.get('tempName')
                action = act.get('action')
                if tempName not in lineInfo:
                    lineErrors.append(_(
                        "Line %(num)d:  The definition of '%(aname)s' is not found.",
                        aname=tempName,
                        num=params['firstLineInfo'][tempName]))
                elif action == '':
                    lineErrors.append(_("Line %(num)d: Action cannot be emptied.",
                                        num=lineInfo[tempName]))
                elif not self._action_name_re.match(action):
                    lineErrors.append(_(
                        "Line %(num)d: Use alphanumeric, dash, and underscore "
                        "characters in the action name.",
                        num=lineInfo[tempName]))
                elif action in actionNames:
                    lineErrors.append(_(
                        "Line %(num)d: Action name is duplicated. The name "
                        "must be unique.",
                        num=lineInfo[tempName]))
                elif not 'next' in act:
                    lineErrors.append(_("Line %(num)d: No next status.",
                                        num=lineInfo[tempName]))
                elif not act['next'] in params['status'] and act['next'] != '*':
                    lineErrors.append(_(
                        "Line %(num)d: '%(status)s' is invalid next status.",
                        num=lineInfo[tempName], status=act['next']))
                elif not act.get('before'):
                    lineErrors.append(_("Line %(num)d: Statuses is empty.",
                                        num=lineInfo[tempName]))
                else:
                    for stat in act['before']:
                        if not stat in params['status'] and stat != '*':
                            lineErrors.append(_(
                                "Line %(num)d: Status '%(status)s' is invalid.",
                                num=lineInfo[tempName], status=stat))

                if 'operations' in act:
                    lineErrors.extend(_("Line %(num)d: Unknown operator.",
                                        num=lineInfo[tempName + '.operations'])
                                      for operation in act['operations']
                                      if operation not in operations)
                if 'permissions' in act:
                    lineErrors.extend(_("Line %(num)d: Unknown permission.",
                                        num=lineInfo[tempName + '.permissions'])
                                      for perm in act['permissions']
                                      if not perm in perms)
                if 'default' in act and act['default'] == -1:
                    lineErrors.append(_(
                        "Line %(num)d: specify a numerical value to 'default'.",
                        num=lineInfo[tempName + '.default']))

                if len(lineErrors) == 0:
                    key = action
                    if 'before' in act:
                        tmp = []
                        for stat in params['status']:
                            if stat in act['before']:
                                tmp.append(stat)
                        before = ','.join(tmp)
                    else:
                        before = '*'

                    newOptions[key] = before + ' -> ' + act['next']
                    newOptions[key + '.name'] = act['name']
                    newOptions[key + '.default'] = act['default']
                    if not 'All Users' in act['permissions']:
                        newOptions[key + '.permissions'] = ','.join(act['permissions'])
                    if act.get('operations'):
                        newOptions[key + '.operations'] = ','.join(act['operations'])
                    if action in params['others']:
                        for otherKey, otherValue in params['others'][action].iteritems():
                            newOptions[key + '.' + otherKey] = otherValue
                else:
                    errors.extend(lineErrors)
                actionNames.append(action)

            count = 1
            for stat in params['status']:
                if len(stat) == 0:
                    errors.append(_("Status column %(num)d: Status name is empty.",
                                    num=count))
                elif ';' in stat or '#' in stat:
                    errors.append(_(
                        "Status column %(num)d: The characters '#' and ';' "
                        "cannot be used for status name.", num=count))
                if stat in params['status'][:count - 1]:
                    errors.append(_(
                        "Status column %(num)d: Status name is duplicated. "
                        "The name must be unique.", num=count))
                count += 1
        return newOptions, errors

    def _update_workflow(self, req, params):
        newOptions, errors = self._validate_workflow(req, params)
        out = {}
        if len(errors) != 0:
            out['result'] = 1
            out['errors'] = errors
        else:
            try:
                for (name, value) in self.config.options('ticket-workflow'):
                    self.config.remove('ticket-workflow', name)
                out['result'] = 0
                for key in newOptions.keys():
                    self.config.set('ticket-workflow', key, newOptions[key])
                self.config.save()
            except Exception, e:
                self.config.parse_if_needed(force=True)
                out['result'] = 1
                out['errors'] = [e.message]
        req.send(json.dumps(out)) # not return

    def _parse_request(self, req):
        params = json.loads(req.args.get('params'))
        if not 'mode' in params:
            return
        if 'text' in params:
            self._str_to_inner_format(params['text'], params)
        else:
            self._json_to_inner_format(params)
        if params['mode'] == 'update':
            self._update_workflow(req, params) # not return
        elif params['mode'] == 'init':
            self._initialize_workflow(req)
        elif params['mode'] == 'reset':
            pass
        elif params['mode'] == 'update-chart':
            self._update_diagram(req, params) # not return
        elif params['mode'] == 'change-textmode':
            req.args['editor_mode'] = 'text'
        elif params['mode'] == 'change-guimode':
            req.args['editor_mode'] = 'gui'
