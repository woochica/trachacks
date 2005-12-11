##########################################################################
#
# debianNeedVersion.py: shows the package version for each Debian suite
#
# This macro receive a Debian package name, a comparison symbol and a
# package version. It returns the found versions for each Debian suite,
# where green names are for satisfied versions and red names are for
# unsitisfied versions. (based on the given version as parameter)
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
# Author: Tiago Bortoletto Vaz <tiago@debian-ba.org>
#

import re,urllib,apt_pkg,string;

apt_pkg.InitConfig();
apt_pkg.InitSystem();

def uniq(alist): 
    set = {}
    map(set.__setitem__, alist, [])
    return set.keys()

def getNeedVersion(args):
    """
    in: (package,[>>,>,<<,<,==],version)
    out: package versions for each Debian suite, green color to satisfied version and
         red color unsatisfied version
    """
    arg=args.split('|')
    package=arg[0]
    symbol=arg[1]
    my_version=arg[2]

    f = urllib.urlopen("http://packages.debian.org/%s" % package)
    html = f.read()
    all = re.compile("""<li><a href="/.*/.*">[a-z]+</a>.*\n<br>.*</li>""",re.DOTALL)
    all2 = re.compile("""<br>.*:""")
    parsed1 = re.sub('href="','href="http://packages.debian.org',all.findall(html)[0])

    for version in uniq(all2.findall(parsed1)):
        version_tmp = version.replace("<br>","")
        version_tmp2 = version_tmp.replace(":","")
        parsed1 = parsed1.replace(version_tmp2,"<font color=\"red\">" + version_tmp2 + "</font>")
        if (cmp(symbol,"==") == 0 or cmp(symbol,"<<") == 0 or cmp(symbol,">>") == 0) and apt_pkg.VersionCompare(my_version,version_tmp2) == 0:
            parsed1 = parsed1.replace(version_tmp2,"<font color=\"green\">" + version_tmp2 + "</font>")
        if (cmp(symbol,">") == 0 or cmp(symbol,">>") == 0) and apt_pkg.VersionCompare(my_version,version_tmp2) < 0:
            parsed1 = parsed1.replace(version_tmp2,"<font color=\"green\">" + version_tmp2 + "</font>")
        if (cmp(symbol,"<") == 0 or cmp(symbol,"<<") == 0) and apt_pkg.VersionCompare(my_version,version_tmp2) > 0:
            parsed1 = parsed1.replace(version_tmp2,"<font color=\"green\">" + version_tmp2 + "</font>")

    return parsed1

def execute(hdf,args,env):
    return getNeedVersion(args)
