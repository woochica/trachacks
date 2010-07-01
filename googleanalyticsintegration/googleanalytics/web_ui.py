# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2008 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# ==============================================================================

from genshi.filters.transform import Transformer

from trac.config import Option
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import Chrome

class GoogleAnalyticsStreamFilter(Component):
    config = env = log = None
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter method
    def filter_stream(self, req, method, filename, stream, data):
        if req.path_info.startswith('/admin'):
            return stream

        options = self.get_options()
        if not options.get('uid'):
            self.log.debug('Plugin not configured, returning stream')
            return stream
        elif ('TRAC_ADMIN' in req.perm) and (not options['admin_logging']):
            self.log.debug("Not tracking TRAC_ADMIN's, returning stream")
            return stream
        elif (req.authname and req.authname != "anonymous") \
                                    and (not options['authenticated_logging']):
            self.log.debug("Not tracking authenticated users, returning stream")
            return stream

        template = Chrome(self.env).load_template('google_analytics.html')
        data = template.generate(
            admin= 'TRAC_ADMIN' in req.perm,
            opt=options,
            base_url='http:\/\/%s' % req.environ.get('HTTP_HOST'))
        return stream | Transformer('body').append(data)

    def get_options(self):
        options = {}
        for option in [option for option in Option.registry.values()
                       if option.section == 'google.analytics']:
            if option.name in ('admin_logging', 'authenticated_logging',
                               'outbound_link_tracking'):
                value = self.config.getbool('google.analytics', option.name,
                                            option.default)
                option.value = value
            elif option.name == 'extensions':
                value = self.config.get('google.analytics', option.name,
                                        option.default)
                option.value = '|'.join(val.strip() for val in value.split(','))
            else:
                value = self.config.get('google.analytics', option.name,
                                        option.default)
                option.value = value
            options[option.name] = option.value
        return options

