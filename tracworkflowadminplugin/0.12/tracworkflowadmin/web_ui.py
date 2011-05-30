# -*- coding:utf-8 -*-
import os
import re
import time
import glob
import shutil
from tempfile import mkstemp
from subprocess import Popen, PIPE
from pkg_resources import resource_filename
try:
    import json
except ImportError:
    import simplejson as json

from trac.core import Component, implements
from trac.config import Option, BoolOption, ListOption, FloatOption
from trac.env import IEnvironmentSetupParticipant
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from trac.admin import IAdminPanelProvider
from trac.util.compat import md5
from trac.util.translation import dgettext, domain_functions

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

    msgjs_locales = _msgjs_locales()
    _action_name_re = re.compile(r'\A[A-Za-z0-9_]+\Z')

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
        yield ('ticket', dgettext("messages", ("Ticket System")),
               'workflowadmin', _("Workflow Admin"))

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('TRAC_ADMIN')
        errors = False
        if req.method == 'POST':
            self._parse_request(req)

        statuses = []
        for name, value in self.config.options('ticket-workflow'):
            if name.endswith('.operations') and value == 'leave_status':
                value = self.config.get('ticket-workflow', name[0:-11])
                statuses.extend(name.strip() for name in value.split('->')[0].split(','))
        statuses_set = set(statuses)
        actions = {}

        for name, value in self.config.options('ticket-workflow'):
            param = name.split('.')
            actionName = param[0].strip()
            regValue = ''
            regKey = ''
            if len(param) == 1:
                regKey = 'status'
                pieces = [val.strip() for val in value.split('->')]
                before = pieces[0]
                next = '*'
                if len(pieces) > 1:
                    next = pieces[1]
                regValue = {'next': next, 'before': {}}
                if next != '*':
                    if next not in statuses_set:
                        statuses.append(next)
                        statuses_set.add(next)
                for val in value.split('->')[0].split(','):
                    tmp = val.strip()
                    regValue['before'][tmp] = 1
                    if tmp != '*':
                        statuses_set.add(tmp)
            else:
                regKey = param[1].strip()
                if regKey == 'permissions' or regKey == 'operations':
                    tmp = []
                    for v in value.strip().split(','):
                        tmp.append(v.strip())
                    regValue = tmp
                else:
                    regValue = value.strip()
            if not actions.has_key(actionName):
                actions[actionName] = {}
            actions[actionName][regKey] = regValue

        action_elements = []
        for key in actions:
            tmp = actions[key]
            tmp['actionName'] = key
            if not tmp.has_key('default'):
                tmp['default'] = 0
            if not tmp.has_key('permissions'):
                tmp['permissions'] = 'All Users'
            action_elements.append(tmp)
        action_elements.sort(cmp=lambda x, y: cmp(int(x['default']), int(y['default'])), reverse=True)

        operations = self.operations
        permissions = self._get_permissions(req)
        add_stylesheet(req, 'tracworkflowadmin/themes/base/jquery-ui.css')
        add_stylesheet(req, 'tracworkflowadmin/css/tracworkflowadmin.css')
        add_stylesheet(req, 'tracworkflowadmin/css/jquery.multiselect.css')
        add_script(req, 'tracworkflowadmin/scripts/jquery-ui.js')
        add_script(req, 'tracworkflowadmin/scripts/jquery.json-2.2.js')
        add_script(req, 'tracworkflowadmin/scripts/jquery.multiselect.js')
        add_script(req, 'tracworkflowadmin/scripts/main.js')
        if req.locale and str(req.locale) in self.msgjs_locales:
            add_script(req, 'tracworkflowadmin/scripts/messages/%s.js' % req.locale)
        data = {
            'actions': action_elements,
            'status': statuses,
            'perms': permissions,
            'operations': operations,
        }
        return 'tracworkflowadmin.html', data

    def _get_permissions(self, req):
        permissions = ['All Users']
        ticket_perms = []
        other_perms = []
        for perm in req.perm.permissions():
            if perm.startswith('TICKET_'):
                ticket_perms.append(perm)
            else:
                other_perms.append(perm)
        ticket_perms.sort()
        other_perms.sort()
        permissions.extend(ticket_perms)
        permissions.extend(other_perms)
        return permissions

    def _create_dot_script(self, params):
        def dot_escape(text):
            return text.replace('\\', '\\\\').replace('"', '\\"')

        script = u'digraph workflow {\n'
        size = self.diagram_size.split(',')
        colors = self.diagram_colors

        script += ' size="%d, %d";\n' % (int(size[0]), int(size[1]))
        statusRev = {}
        for idx, stat in enumerate(params['status']):
            script +=  ' node_%d [label="%s"' % (idx, dot_escape(stat))
            if self.diagram_font:
                script += ', fontname="%s"' % dot_escape(self.diagram_font)
            script +=  ', fontsize="%g"];\n' % self.diagram_fontsize
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
        script = self._create_dot_script(params)
        self._image_path_setup(req)
        dir = os.path.join(self.env.get_htdocs_dir(), 'tracworkflowadmin')
        basename = '%s.png' % md5(script).hexdigest()
        path = os.path.join(dir, basename)
        if self.diagram_cache and os.path.isfile(path):
            os.utime(path, None)
        else:
            tmpfd, tmppath = mkstemp(suffix='.png', dir=dir)
            os.close(tmpfd)
            proc = Popen([self.dot_path, '-Tpng', '-o', tmppath], stdin=PIPE)
            proc.stdin.write(script)
            proc.stdin.close()
            proc.wait()
            try:
                os.remove(path)
            except:
                pass
            os.rename(tmppath, path)
        _, errors = self._validate_workflow(req, params)
        data = {'result': (1, 0)[len(errors) == 0],     # 0 if cond else 1
                'errors': errors,
                'image_url': self._image_tmp_url(req, basename)}
        req.send(json.dumps(data))
        # NOTREACHED

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
        errors = []
        if not 'actions' in params:
            errors.append(_("Invalid request without actions. Please restart your browser and retry."))
        if len(params['actions']) == 0:
            errors.append(_("Need at least one action."))
        if not 'status' in params:
            errors.append(_("Invalid request without statuses. Please restart your browser and retry."))
        if len(params['status']) == 0:
            errors.append(_("Need at least one status."))

        if len(errors) == 0:
            perms = self._get_permissions(req)
            operations = self.operations
            count = 1
            actionNames = []
            newOptions = {}
            for act in params['actions']:
                lineErrors = []
                if not act.get('action'):
                    lineErrors.append(_("Line %(num)d: No action name", num=count))
                elif not self._action_name_re.match(act['action']):
                    lineErrors.append(_("Line %(num)d: Action names can contain only alphabetic and numeric characters.",
                                        num=count))
                elif act['action'] in actionNames:
                    lineErrors.append(_("Line %(num)d: Action name is duplicated. The name must be"
                                        " unique.",
                                        num=count))
                if not act.get('name'):
                    lineErrors.append(_("Line %(num)d: No display name.", num=count))
                for operation in act['operations']:
                    if not operation in operations:
                        lineErrors.append(_("Line %(num)d: Unknown operator.", num=count))
                for perm in act['permissions']:
                    if not perm in perms:
                        lineErrors.append(_("Line %(num)d: Unknown permission.", num=count))
                if not 'next' in act:
                    lineErrors.append(_("Line %(num)d: No next status.", num=count))
                elif not act['next'] in params['status'] and act['next'] != '*':
                    lineErrors.append(_("Line %(num)d: '%(status)s' is invalid next status.",
                                        num=count, status=act['next']))
                if not act.get('before'):
                    lineErrors.append(_("Line %(num)d: Statuses is empty.", num=count))
                else:
                    for stat in act['before']:
                        if not stat in params['status'] and stat != '*':
                            lineErrors.append(_("Line %(num)d: Status '%(status)s' is invalid.",
                                                num=count, status=stat))
                if len(lineErrors) == 0:
                    key = act['action']
                    if act['before']:
                        before = ','.join(act['before'])
                    else:
                        before = '*'

                    newOptions[key] = before + ' -> ' + act['next']
                    newOptions[key + '.name'] = act['name']
                    newOptions[key + '.default'] = act['default']
                    if not 'All Users' in act['permissions']:
                        newOptions[key + '.permissions'] = ','.join(act['permissions'])
                    newOptions[key + '.operations'] = ','.join(act['operations'])
                else:
                    errors.extend(lineErrors)
                actionNames.append(act['action'])
                count += 1
            count = 1
            for stat in params['status']:
                if len(stat) == 0:
                    errors.append(_("Status column %(num)d: Status name is empty.", num=count))
                elif ';' in stat or '#' in stat:
                    errors.append(_("Status column %(num)d: The characters '#' and ';' cannot be used for status name.",
                                    num=count))
                if stat in params['status'][:count - 1]:
                    errors.append(_("Status column %(num)d: Status name is duplicated. The name"
                                    " must be unique.",
                                    num=count))
                count += 1
        return newOptions, errors

    def _update_workflow(self, req, params):
        newOptions, errors = self._validate_workflow(req, params)
        out = {}
        if len(errors) != 0:
            out['result'] = 1
            out['errors'] = errors
        else:
            for (name, value) in self.config.options('ticket-workflow'):
                self.config.remove('ticket-workflow', name)
            out['result'] = 0
            for key in newOptions.keys():
                self.config.set('ticket-workflow', key, newOptions[key])
            self.config.save()
        req.send(json.dumps(out)) # not return

    def _parse_request(self, req):
        params = json.loads(req.args.get('params'))
        if not 'mode' in params:
            return
        if params['mode'] == 'update':
            self._update_workflow(req, params) # not return
        elif params['mode'] == 'init':
            self._initialize_workflow(req)
        elif params['mode'] == 'reset':
            pass
        elif params['mode'] == 'update-chart':
            self._update_diagram(req, params) # not return
