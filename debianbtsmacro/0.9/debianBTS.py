##########################################################################
#
# debianBTS.py: macro for Trac to show Debian Bug tracking system info
#
# Debian BTS receive a bug number, a maintainer's email or a package name
# and show a link to their respective Debian Bug tracking system page
# See http://trac-hacks.swapoff.org/wiki/DebianBtsMacro
#
# ====================================================================
# Copyright (c) 2005 Debian-BR-CDD Team.  All rights reserved.
#
#   This package is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; version 2 dated June, 1991.
#
#   This package is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this package; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
#   02111-1307, USA.
#
#########################################################################
# Authors: Tiago Bortoletto Vaz <tiago@debian-ba.org>
#

import re

def getDebString(args):
    """
    in: a bug number, a maintainer email or a package name
    out: a link to BTS
    """

    bts_url="http://bugs.debian.org/cgi-bin/pkgreport.cgi?"
    mail_pattern=r'^(([A-Za-z0-9]+_+)|([A-Za-z0-9]+\-+)|([A-Za-z0-9]+\.+)|([A-Za-z0-9]+\++))*[A-Za-z0-9]+@((\w+\-+)|(\w+\.))*\w{1,63}\.[a-zA-Z]{2,6}$' #by Eric Wise

    if args.isalpha(): # if we have a package
        return "<a href=\""+bts_url+"pkg="+args+"\">"+args+"</a>"
    elif args.isdigit(): # if we have a bug
        return "<a href=\""+bts_url+"bug="+args+"\">"+args+"</a>"
    elif re.match(mail_pattern,args): # if we have a maintainter mail address
        return "<a href=\""+bts_url+"maint="+args+"\">"+args+"</a>"

def execute(hdf,args,env):
    return getDebString(args)
