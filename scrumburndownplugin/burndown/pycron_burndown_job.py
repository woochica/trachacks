# Copyright (C) 2006 Sam Bloomquist <samuel.bloomquist@libertymutual.com>
# All rights reserved.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Author: Christopher Lenz <cmlenz@gmx.de>

import time
from trac.core import *
from trac.util import format_datetime, http_date

    def display_rss(self, req, query):
        query.verbose = True
        db = self.env.get_db_cnx()
        results = query.execute(db)
        for result in results:
            result['href'] = self.env.abs_href.ticket(result['id'])
            if result['reporter'].find('@') == -1:
                result['reporter'] = ''
            if result['description']:
                # str() cancels out the Markup() returned by wiki_to_html
                descr = wiki_to_html(result['description'], self.env, req, db,
                                     absurls=True)
                result['description'] = str(descr)
            if result['time']:
                result['time'] = http_date(result['time'])
        req.hdf['query.results'] = results
        req.hdf['query.href'] = self.env.abs_href.query(group=query.group,
                groupdesc=query.groupdesc and 1 or None,
                verbose=query.verbose and 1 or None,
                **query.constraints)