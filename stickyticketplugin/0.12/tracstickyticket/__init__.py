# -*- coding: utf-8 -*-

from pkg_resources import DistributionNotFound, get_distribution

NAME = 'StickyTicketPlugin'
try:
    VERSION = get_distribution(NAME).version
except DistributionNotFound:
    VERSION = '0.12.0.3'
