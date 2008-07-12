# -*- coding: utf-8 -*-
"""
    Trac SQLAlchemy Bridge
    ======================

    tracext.sa
    ~~~~~~~~~~

    This module enables a plugin developer to use SQLAlchemy for database work.

    For some usage example there's nothing better than `source code`__.

    :copyright: 2008 by Armin Ronacher, Pedro Algarvio.
    :license: WTFPL.


    .. __: http://tl10nm.ufsoft.org/browser

"""
#            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#                    Version 2, December 2004
#
# Copyright (C) 2008 Armin Ronacher, Pedro Algarvio.
#  14 rue de Plaisance, 75014 Paris, France
# Everyone is permitted to copy and distribute verbatim or modified
# copies of this license document, and changing it is allowed as long
# as the name is changed.
#
#            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
#
#  0. You just DO WHAT THE FUCK YOU WANT TO.
#
# http://en.wikipedia.org/wiki/WTFPL
#
# Authors:
#    Armin Ronacher <armin.ronacher@active-4.com>
#    Pedro Algarvio <ufs@ufsoft.org>

__version__     = '0.1.0'
__author__      = 'Armin Ronacher, Pedro Algarvio'
__email__       = 'armin.ronacher@active-4.com, ufs@ufsoft.org'
__package__     = 'TracSQLAlchemyBridge'
__license__     = 'WTFPL'
__url__         = 'http://trac-hacks.org/wiki/TracSqlAlchemyBridgeIntegration'
__summary__     = 'Bridge for a plugin developer to use SQLAlchemy with trac'
__description__ = __doc__

from weakref import WeakKeyDictionary
from threading import local
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import create_session, scoped_session
from sqlalchemy.pool import NullPool
from sqlalchemy.engine.url import URL
from trac.db.api import DatabaseManager
from trac.db.util import ConnectionWrapper

class DummyPool(NullPool):
    def do_return_conn(self, conn):
        # Don't let SQLAlchemy close the connection, trac handles that
        pass

_engines = WeakKeyDictionary()

def engine(env):
    engine = _engines.get(env)
    if engine is None:
        schema = DatabaseManager(env).connection_uri.split(':')[0]
        echo = env.config.get('logging', 'log_level').lower() == 'debug'

        def connect():
            cnx = env.get_db_cnx().cnx
            while isinstance(cnx, ConnectionWrapper):
                cnx = cnx.cnx
            return cnx

        engine = create_engine(URL(schema), poolclass=DummyPool,
                               creator=connect, echo=echo)
        if echo:
            # make sqlalchemy log to trac's logger
            engine.logger = env.log

            _engines[env] = engine
    return engine


def session(env):
    db_session = create_session(engine(env), transactional=True)
    # Keep session opened for as long as possible by keeping it attached to
    # env; avoids it to be garbage collected since trac explicitly calls gc
    # to avoid memory leaks
    env.db_session = db_session
    return db_session

__all__ = ['engine', 'session']
