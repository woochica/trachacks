#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.web.chrome import ITemplateProvider


class CommonTemplateProvider(Component):
    """Generic template provider."""

    implements(ITemplateProvider)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return [resource_filename('crypto', 'templates')]
