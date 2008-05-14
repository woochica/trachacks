# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         upgrades.py
# Purpose:      The MileMixView admin Trac plugin upgrade module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------


"""Automated upgrades for the rt database tables, and other data stored
in the Trac environment."""

import os
import sys
import time

global ENV

def add_rt_table(env, db):
    """Migrate db."""

    pass
    
map = {
    1: [add_rt_table],
}
