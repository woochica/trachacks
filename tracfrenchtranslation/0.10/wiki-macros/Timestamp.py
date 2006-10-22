# -*- coding: utf-8 -*-
u"""Insère la date actuelle (en secondes) sur la page Wiki."""

import time
def execute(hdf, txt, env):
    t = time.localtime()
    return "<b>%s</b>" % time.strftime('%c', t)
