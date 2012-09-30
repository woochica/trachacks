# -*- coding: utf-8 -*-

import pkg_resources
import re
from datetime import datetime, timedelta

from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant
from trac.timeline.web_ui import TimelineModule
from trac.util.datefmt import format_datetime
from trac.util.translation import dgettext
from trac.web.api import IRequestFilter
from trac.web.chrome import (
    ITemplateProvider, Chrome, add_script, add_script_data
)
from trac.web.main import RequestDispatcher


class TimeDeltaUpdatorModule(Component):

    implements(IEnvironmentSetupParticipant, ITemplateProvider, IRequestFilter)

    htdocs_dir = pkg_resources.resource_filename(__name__, 'htdocs')
    has_pretty_dateinfo = False

    def __init__(self):
        self.has_pretty_dateinfo = hasattr(Chrome(self.env),
                                           'default_dateinfo_format')

    # IEnvironmentSetupParticipant#environment_created
    def environment_created(self):
        pass

    # IEnvironmentSetupParticipant#environment_needs_upgrade
    def environment_needs_upgrade(self, db):
        if not self.has_pretty_dateinfo:
            return False

        def find(list, val):
            try:
                return list.index(val)
            except ValueError:
                return len(list)
        filters = RequestDispatcher(self.env).filters
        if find(filters, self) < find(filters, TimelineModule(self.env)):
            return False

        name = self.__class__.__name__
        self.log.warn(
            'Prepend %s to request_filters in [trac] section\n'
            '[trac]\n'
            'request_filters = %s',
            name,
            ','.join([name] + self.config.getlist('trac', 'request_filters')))
        return False

    # IEnvironmentSetupParticipant#upgrade_environment
    def upgrade_environment(self, db):
        pass

    # ITemplateProvider#get_htdocs_dirs
    def get_htdocs_dirs(self):
        return [('tractimedeltaupdator', self.htdocs_dir)]

    # ITemplateProvider#get_templates_dirs
    def get_templates_dirs(self):
        return []

    # IRequestFilter#pre_process_request
    def pre_process_request(self, req, handler):
        return handler

    # IRequestFilter#post_process_request
    def post_process_request(self, req, template, data, content_type):
        if data and (not self.has_pretty_dateinfo or data.get('dateinfo')):
            add_script(req, 'tractimedeltaupdator/main.js')
            if self.has_pretty_dateinfo:
                dateinfo = req.session.get(
                    'dateinfo', Chrome(self.env).default_dateinfo_format)
                script_data = self._get_script_data(req, data, dateinfo)
                self._set_dateinfo_funcs(req, data, dateinfo)
            else:
                script_data = self._get_script_data(req, data, 'relative')
            add_script_data(req, {'tractimedeltaupdator': script_data})
        return template, data, content_type

    def _set_dateinfo_funcs(self, req, data, default):
        pretty_dateinfo_orig = data['pretty_dateinfo']
        if default != 'relative':
            default = 'absolute'

        def pretty_dateinfo(date, format=None, dateonly=False):
            node = pretty_dateinfo_orig(date, format=format, dateonly=dateonly)
            if not node:
                return node
            isodate = format_datetime(date, format='iso8601', tzinfo=req.tz)
            kwargs = {'data_tractimedeltaupdator_format': format or default,
                      'data_tractimedeltaupdator_time': isodate}
            if dateonly:
                kwargs['data_tractimedeltaupdator_dateonly'] = '1'
            return node(**kwargs)

        data['pretty_dateinfo'] = pretty_dateinfo
        data['dateinfo'] = lambda date: \
            pretty_dateinfo(date, format='relative', dateonly=True)

    def _get_script_data(self, req, data, dateinfo):
        plural_forms = self._get_plural_forms()
        script_data = {
            'units': self._get_units(plural_forms[0]),
            'pluralexpr': plural_forms[1],
            'starttime': format_datetime(format='iso8601', tzinfo=req.tz),
        }
        if data.get('pretty_dateinfo'): # 1.0+
            in_future = datetime.now(req.tz) + timedelta(days=1)
            in_future = data['pretty_dateinfo'](in_future, format='absolute',
                                                dateonly=True).tag != 'a'
            absolute = {'past': dgettext('messages',
                                         "See timeline %(relativetime)s ago") \
                                .replace('%(relativetime)s', '%(relative)s')}
            if in_future:
                # 1.1+
                relative = {'past': dgettext('messages', "%(relative)s ago")}
                absolute['future'] = relative['future'] = \
                                        dgettext('messages', "in %(relative)s")
            else:
                absolute['future'] = absolute['past']
                relative = dgettext('messages', "%(relativetime)s ago") \
                           .replace('%(relativetime)s', '%(relative)s')
                relative = {'future': relative, 'past': relative}

            script_data.update({'format': dateinfo, 'relative': relative,
                                'absolute': absolute})
        return script_data

    _plural_forms_re = re.compile(r"""
        Plural-Forms:\s*
        nplurals\s*=\s*(?P<nplurals>\d+);\s*
        plural\s*=\s*(?P<plural>[^;]+)""", re.VERBOSE)

    def _get_plural_forms(self):
        for line in dgettext('messages', "").splitlines():
            match = self._plural_forms_re.match(line)
            if match:
                return (int(match.group('nplurals')), match.group('plural'))
        return (2, 'n != 1')

    def _get_units(self, n):
        def format(msg):
            return [dgettext('messages', (msg, i)) for i in xrange(n)]
        return (
            (3600*24*365, format('%(num)d year')),
            (3600*24*30,  format('%(num)d month')),
            (3600*24*7,   format('%(num)d week')),
            (3600*24,     format('%(num)d day')),
            (3600,        format('%(num)d hour')),
            (60,          format('%(num)d minute')),
            (1,           format('%(num)i second')),
        )
