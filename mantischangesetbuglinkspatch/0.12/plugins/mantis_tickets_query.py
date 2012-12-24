# -- mantis_tickets_query.py
#
# Author: techtonik <techtonik@rainforce.org>
# Date:   2008-10-27
# License: Trac (modified BSD)
# ----------------------------------------------------------------------------

"""
   Replace referenced tickets in cached commit messages with links to external
   Mantis bugtracker.

   Requires:
   * ICacheChangesetListener interface patch
   * Genshi
"""

from trac.core import *
from trac.versioncontrol.cache import ICacheChangesetListener

import genshi
import urllib2
import re

MANTIS_URL = "http://bugs.farmanager.com"
MANTIS_BUG_FMT = "/".join([MANTIS_URL, "view.php?id=%d"])


def genshi_parse(url):
    """parse url content to get issue title
    todo: use html parses that doesn't fail on malformed output

    >>> genshi_parse("http://www.mantisbt.org/bugs/view.php?id=555")
    u'0000555: User partitioning not working - MantisBT'   
    >>> print genshi_parse("http://bugs.farmanager.com/view.php?id=1288")
    None

    :return: issue title or None of malformed input
    """
    title_path = "head/title/text()"
    mbt_file = urllib2.urlopen(url)
    #mbt_genshi = genshi.input.HTML(mbt_file)
    mbt_genshi = genshi.input.HTMLParser(mbt_file)
    try:
        title = mbt_genshi.parse().select(title_path).render().decode("utf-8")
    except genshi.ParseError, err:
        return None
    return title


class MantisChangesetQuery(Component):
    """Change mantis ticket references ("Mantis #xxxxxx") in changeset messages
       to direct links to external Mantis installation. Query Mantis to get
       descriptive link title"""

    implements(ICacheChangesetListener)

    mantis_re = re.compile(r"mantis *#(?P<mbt_number>\d+)", re.I|re.U)
    mantis_re_title = re.compile(r"^\d+: *(?P<mbt_title>.+?)( - Mantis)?$", re.I|re.U)

    def edit_changeset(self, cset):
        self.log.debug("MantisChangesetQuery ICacheChangesetListener edit_changeset")
        matched = self.mantis_re.findall(cset.message)
        if not matched:
            return None
        else:
            # matched is returned as a list of strings with bug numbers
            matched = [int(m) for m in matched]
            bugs_info = {}
            # query Mantis for bug data
            for no in matched:
                bugs_info[no] = dict(no=no, title="")
                url = MANTIS_BUG_FMT % no
                self.log.info("Lookup bug title at Mantis webpage %s" % url)

                title = genshi_parse(url)

                # example  : 0000619: Bug description - Mantis
                # validate : ends with "- Mantis", starts with bug number
                if not title:
                    self.log.warning("Bug title lookup failed %s" % url)
                else:
                    # strip suffix/prefix
                    title = self.mantis_re_title.sub(u"\g<mbt_title>", title)
                    bugs_info[no]["title"] = title

            # to simplify - links are embedded in message comment directly
            # it is also possible to construct a special formatter or macros,
            # but the complication doesn't worth a sole popup-hint feature

            # add links with full descriptions to messages
            def linker(matchobj):
                number = int(matchobj.groupdict().get("mbt_number"))
                return u"[%s %s]: %s" % (MANTIS_BUG_FMT % number, "Mantis#%07d" % number, bugs_info[number]["title"])

            cset.message = self.mantis_re.sub(linker, cset.message)
            return cset


if __name__ == "__main__":
    doc = \
    """Here should be tests for mantis #094 type
       of links as well as for
       Mantis#909
       and the likes. Unfortunately, it requires external site for queries
    """
    r = MantisChangesetQuery.mantis_re
    m = r.findall(doc)
    print m

    import doctest
    doctest.testmod()
