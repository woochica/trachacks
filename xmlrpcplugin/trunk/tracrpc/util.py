# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2008 ::: Alec Thomas (alec@swapoff.org)
(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import datetime
import time
import xmlrpclib

from trac.util.datefmt import utc

def to_xmlrpc_datetime(dt):
    """ Convert a datetime.datetime object to a xmlrpclib DateTime object """
    return xmlrpclib.DateTime(dt.utctimetuple())

def from_xmlrpc_datetime(data):
    """Return datetime (in utc) from XMLRPC datetime string (is always utc)"""
    t = list(time.strptime(data.value, "%Y%m%dT%H:%M:%S")[0:6])
    return apply(datetime.datetime, t, {'tzinfo': utc})
