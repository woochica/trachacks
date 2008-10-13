# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         upgrades.py
# Purpose:      The report manager Trac plugin upgrade module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------


"""Automated upgrades for the report manager database tables, and other data stored
in the Trac environment."""

import os
import sys
import time

def add_reports_table(env, db):
    """Upgrade report manager tables."""
    pass


map = {
    1: [add_reports_table],
}
