# -*- coding: utf-8 -*-
"""
    ircannouncer.api
    ~~~~~~~~~~~~~~~~

    Adds an extra hook the listener listens on.

    :copyright: Copyright 2007 by Armin Ronacher.
    :license: BSD.
"""
from trac.core import *


class ICheckinListener(Interface):
    """
    Extension point interface for components (currently only our own
    component, but would be cool if that interface would be part of
    trac) that require notification when code is checked in.
    """

    def changeset_checked_in(chgset):
        pass
