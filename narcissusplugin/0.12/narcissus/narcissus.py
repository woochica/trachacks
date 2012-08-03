# vim: et
#
# Narcissus plugin for Trac
#
# Copyright (C) 2008 Kim Upton    
# All rights reserved.    
#

import os
import sys
import hashlib
import time
import datetime

import Image
import ImageDraw
import ImageFont

from genshi.builder import tag

from trac.core import *
from trac.perm import IPermissionRequestor
from trac.util.datefmt import format_date
from trac.web.chrome import INavigationContributor
from trac.web.main import IRequestHandler
from trac.util import escape
from trac import mimeview
from trac.ticket.model import Ticket
from trac.wiki.model import WikiPage
from trac.versioncontrol.diff import diff_blocks

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from settings import NarcissusSettings

_TRUE_VALUES = ('yes', 'true', 'on', 'aye', '1', 1, True)
_CMD_PATHS = {'linux2': '/usr/bin',
              'win32': 'c:\\Program Files\\ATT\\Graphviz\\bin',
              'freebsd6': '/usr/local/bin',
              'freebsd5': '/usr/local/bin',
              'darwin': '/opt/local/bin/',
             }
# purple; blue; green; yellow; orange; red; grey;
_RED = [189, 20, 23, 230, 230, 204, 128]
_GREEN = [23, 105, 230, 230, 145, 41, 128]
_BLUE = [230, 230, 107, 23, 5, 36, 128]
_SQUARE_SIZE = 25
_TICKET_MIN = 6
_TICKET_MAX = 10
_SCREEN_SPACE = 500

MICROSECONDS_SECOND = 1000000
MICROSECONDS_DAY = 24 * 60 * 60 * MICROSECONDS_SECOND

class NarcissusPlugin(Component):
    implements(IPermissionRequestor, INavigationContributor, IRequestHandler)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['NARCISSUS_VIEW']

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'narcissus'

    def get_navigation_items(self, req):
        if req.perm.has_permission('NARCISSUS_VIEW'):
            yield 'mainnav', 'narcissus', tag.a('Narcissus',
                href=self.env.href.narcissus())

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/narcissus'

    def process_request(self, req):
        req.perm.assert_permission('NARCISSUS_VIEW')

        img = req.args.get('img', None)
        if img:
            self._load_config()
            img_path = os.path.join(self.cache_dir, img)
            return req.send_file(img_path, mimeview.get_mimetype(img_path))
        
        params = {}
        params['page'] = 'narcissus'
        params['href_narcissus'] = self.env.href.narcissus()
        params['href_configure'] = self.env.href.narcissus('configure')
        params['href_user_guide'] = self.env.href.narcissus('user_guide')
        params['error'] = None
        params['msg'] = ""
        
        self.db = self.env.get_db_cnx()

        self._settings = NarcissusSettings(self.db)
        
        # Ensure Narciussus has been configured to incluude some group members
        if not self._settings.members:
            params['msg'] = '''No group members have been selected for visualisation.
                Please add group members using the configuration page.'''
            return 'narcissus.xhtml', params, None
        
        # Parse the from date and adjust the timestamp to the last second of
        # the day (taken from Timeline.py, (c) Edgewall Software)
        t = time.localtime()
        if req.args.has_key('from'):
            try:
                t = time.strptime(req.args.get('from'), '%x')
            except:
                pass

        fromdate = time.mktime((t[0], t[1], t[2], 23, 59, 59, t[6], t[7], t[8]))
        try:
            daysback = max(0, int(req.args.get('daysback', '')))
        except ValueError:
            daysback = 14 # Default value of one fortnight
        params['date_end'] = fromdate
        params['date_from'] = format_date(fromdate)
        params['date_daysback'] = daysback
        
        self._update_data(req)
        self._create_legend(req, params)
        
        trouble, msg = self._get_font()
        if trouble:
            params['error'] = msg.getvalue()
        else:
            view = req.args.get('view', 'group')
            params['view'] = view
            if view == 'group':
                self._draw_group(req, params)
            elif view == 'project':
                self._draw_project(req, params),
            elif view == 'ticket':
                self._draw_ticket(req, params)

        #print>>sys.stderr, 'return request'
        return 'narcissus.xhtml', params, None

    # Data extraction methods
    def _update_data(self, req):
        # Update narcissus_data table with info to be visualised
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        cursor.execute('select max(dtime) from narcissus_data')
        start_rev = 1
        last_update = cursor.fetchone()[0]
        if not last_update:
            # no data yet, update data from the beginning
            cursor.execute('select min(time) from wiki')
            last_update = cursor.fetchone()[0]
        else:
            # update data from this change
            cursor.execute('select eid from narcissus_data where resource = "svn"')
            for row in cursor:
                if int(row[0]) > start_rev:
                    start_rev = int(row[0])
            start_rev += 1
        members = self._settings.members
        
        # populate table with wiki activity
        cursor.execute('''select name, min(version), count(version), min(time) from wiki
            where time > %f group by name order by min(time)''' % last_update)
        for page, start_version, versions, _ in cursor:
            versions += start_version
            # page has been added
            if start_version == 1:
                new_page = WikiPage(self.env, page, 1)
                add = len(new_page.text.splitlines())
                if (new_page.author in members) and (self._to_microseconds(new_page.time) > last_update):
                    self._insert_data(new_page.author, new_page.time, 
                        new_page.name, 'wiki', 'add', add)
                start_version += 1
            for i in xrange(start_version, versions):
                # page has been edited
                old_page, edit_page = WikiPage(self.env, page, i - 1), WikiPage(self.env, page, i)
                if (edit_page.author in members) and (self._to_microseconds(edit_page.time) > last_update):
                    changes = self._my_diff(old_page.text, edit_page.text)
                    edit = self._edit_newlines(changes)
                    if edit:
                        self._insert_data(edit_page.author, edit_page.time, 
                            edit_page.name, 'wiki', 'edit', edit)

        # populate table with ticket activity
        credits = self._settings.credits
        cursor.execute('select id from ticket')
        for row in cursor:
            ticket = Ticket(self.env, row[0])
            # ticket has been opened
            if ticket['reporter'] in members and self._to_microseconds(ticket.time_created) > last_update:
                self._insert_data(ticket['reporter'], ticket.time_created, 
                    ticket.id, 'ticket', 'open', 1) # FIXME
            for dtime, author, field, _, newvalue, _ in ticket.get_changelog():
                if author in members and self._to_microseconds(dtime) > last_update:
                    if field == 'comment':
                        # ticket has received comment
                        self._insert_data(author, dtime, ticket.id, 
                            'ticket', 'comment', credits['comment'])
                    elif newvalue == 'assigned':
                        # ticket has been accepted
                        self._insert_data(author, dtime, ticket.id, 
                            'ticket', 'accept', credits['accept'])
                    elif field == 'resolution':
                        # ticket has been closed, reopened closures only count as a change
                        reopened = False
                        for inner_time, _, _, _, _, _ in ticket.get_changelog():
                            if inner_time > dtime and field == 'resolution':
                                reopened = True
                        if reopened:
                            self._insert_data(author, dtime, ticket.id, 
                                'ticket', 'update', credits['update'])
                        else:
                            if ticket['owner'] in members:
                                self._insert_data(ticket['owner'], dtime, 
                                    ticket.id, 'ticket', 'close', credits['close'])
                            if author != ticket['owner']:
                                self._insert_data(author, dtime, ticket.id, 
                                    'ticket', 'proxy close', credits['update'])
                    else:
                        # ticket has been changed
                        self._insert_data(author, dtime, ticket.id, 
                            'ticket', 'update', 1) # FIXME

        # populate table with svn activity
        repos = self.env.get_repository()
        youngest_rev = str(repos.youngest_rev or 0).split(':')[0]

        try:
            youngest_rev = int(youngest_rev) + 1
        except:
            youngest_rev = 0

        for rev in xrange(start_rev, youngest_rev):
            cs = repos.get_changeset(rev)
            add, edit = 0, 0
            for path, _, change, base_path, base_rev in cs.get_changes():
                if change == 'add':
                    add += self._svn_add_newlines(repos, path, rev)
                elif change == 'edit':
                    diff_args = {'old_path': base_path,
                                 'old_rev': base_rev, 
                                 'new_path': path or '/', 
                                 'new_rev': rev
                                }
                    changes = self._my_svn_diff(repos, diff_args)
                    if changes:
                        edit += self._edit_newlines(changes)

            valid_user = cs.author in members
            if not valid_user:
                for u, n, e in self.env.get_known_users():
                    if e != None and e in cs.author:
                        valid_user = True

            if add and valid_user:
                self._insert_data(cs.author, cs.date, rev, 'svn', 'add', add)
            if edit and valid_user:
                self._insert_data(cs.author, cs.date, rev, 'svn', 'edit', edit)
        db.commit()

    def _insert_data(self,  member, dtime, eid, resource, dtype, value):
        # Insert a row into the narcissus_data table
        cursor = self.db.cursor()
        insert = "insert into narcissus_data values ('%s', %d, '%s', '%s', '%s', %d)"\
            % (member, self._to_microseconds(dtime), str(eid).replace("'", ""), resource, dtype, value)
        #print>>sys.stderr, insert
        cursor.execute(insert)

    # Drawing and visualisation methods
    def _create_legend(self, req, params):
        # Create images and text for legend
        img = Image.new("RGBA", (15, 15), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        view = req.args.get('view', 'group')

        if view == 'group' or view == 'project':
            legend = self._settings.resources
        elif view == 'ticket':
            legend = self._settings.members

        items = []
        for j, leg in enumerate(legend):
            draw.rectangle([0, 0, 14, 14], fill=(_RED[j%len(_RED)], _GREEN[j%len(_GREEN)], _BLUE[j%len(_BLUE)], 255))
            obj = self._cache_image(req, params, img, "%s%d" % (leg, j))
            if obj is None:
                return
            obj['name'] = leg
            items.append(obj)
        params['legend'] = items

    def _draw_group(self, req, params):
        # Draw image and generate data for image map for group view
        start, end, days = self._get_dates(params)
        members = self._settings.members
        resources = self._settings.resources
        cursor = self.db.cursor()

        date_offset, name_offset = 80, 30
        # determine width of graph
        bars = len(members) * len(resources) * _SQUARE_SIZE
        gaps = len(members) * 2 * _SQUARE_SIZE
        page_width = date_offset + bars + gaps
        # determine height of graph
        summary_scale = _SQUARE_SIZE / 4
        summary_height = int(2 * days * summary_scale)
        page_height = name_offset + (days * _SQUARE_SIZE) + summary_height

        img = Image.new("RGBA", (page_width, page_height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        layer = Image.new("RGBA", (page_width, page_height), (255, 255, 255, 0))
        drawtop = ImageDraw.Draw(layer)

        draw = self._write_dates((0, page_height - summary_height), start, days, draw)

        # draw individual squares
        map = []
        totals = {}
        averages = [0, 0, 0]
        colw, colh = len(resources) * _SQUARE_SIZE, days * _SQUARE_SIZE
        for m, mem in enumerate(members):
            totals[mem] = [0, 0, 0]
            memx = date_offset + (m * (len(resources) + 2) * _SQUARE_SIZE)
            x, y = memx, page_height - summary_height
            draw.rectangle([x, y, x + colw - 1, y - colh + 1], fill=(229, 229, 229, 255))
            idate = start
            for i in range(days):
                for j, res in enumerate(resources):
                    statement = '''select sum(value) from narcissus_data where
                        member = "%s" and resource = "%s" and dtime >= %s and 
                        dtime < %s''' % (mem, res, idate, 
                        idate + MICROSECONDS_DAY)
                    cursor.execute(statement)
                    total_value = cursor.fetchone()[0]
                    if total_value:
                        y = page_height - summary_height - self._date_y(start, idate)
                        jx = x + (j * _SQUARE_SIZE)
                        score = self._get_score(res, total_value)
                        totals[mem][j] += score
                        averages[j] += score
                        drawtop.rectangle([jx, y, jx + _SQUARE_SIZE - 1, y - _SQUARE_SIZE + 1],
                            fill=(_RED[j], _GREEN[j], _BLUE[j], score * 0.25 * 255))
                        # add info for the template to render an image map
                        idx = '%s_%s_%s' % (mem, res, idate)
                        href = '%s/details?member=%s&resource=%s&date=%s'\
                            % (req.base_url, mem, res, idate)

                        item = {}
                        item['href'] = href
                        item['x1'] = jx
                        item['y1'] = y - _SQUARE_SIZE
                        item['x2'] = jx + _SQUARE_SIZE
                        item['y2'] = y
                        map.append(item)
                idate += MICROSECONDS_DAY

            # print member names
            x, y = memx + 10, name_offset * 0.4
            draw.text((x, y), mem, fill=(0, 0, 0, 255), font=self._ttf)

        params['mapItems'] = map


        # draw summary bars
        for i, a in enumerate(averages):
            averages[i] = a / len(members)
        for m, mem in enumerate(members):
            mx = date_offset + (m * (len(resources) + 2) * _SQUARE_SIZE)
            y = page_height - summary_height + (_SQUARE_SIZE / 2)
            for r, res in enumerate(resources):
                rx = mx + (r * _SQUARE_SIZE)
                if totals[mem][r]:
                    draw.rectangle([rx, y + int(summary_scale * totals[mem][r]), 
                                   rx + _SQUARE_SIZE - 1, y + 1],
                                   fill=(_RED[r], _GREEN[r], _BLUE[r], 255))
                if averages[r]:
                    drawtop.rectangle([rx, y + int(summary_scale * averages[r]),
                                      rx + _SQUARE_SIZE - 1, y + 1],
                                      fill=(0, 0, 0, 52))

        img = Image.composite(layer, img, layer)
        params['vis'] = self._cache_image(req, params, img, 'vis')

    def _draw_project(self, req, params):
        # Draw image and generate data for image map for project view
        start, end, days = self._get_dates(params)
        members = self._settings.members
        resources = self._settings.resources
        cursor = self.db.cursor()

        # calculate totals for column widths
        widths = [0, 0, 0]
        for r, res in enumerate(resources):
            idate = start
            for i in range(days):
                jdate = idate + MICROSECONDS_DAY
                statement = '''select sum(value) from narcissus_data where
                    resource = "%s" and dtime >= %s and dtime < %s'''\
                    % (res, idate, jdate)
                cursor.execute(statement)
                value = cursor.fetchone()[0]
                if value:
                    widths[r] += self._get_score(res, int(value))
                idate = jdate
        
        total_width = 0
        for i, w in enumerate(widths):
            if w > 0: widths[i] = int((float(w) / days) * 100) + (_SQUARE_SIZE / 2)
            total_width += widths[i]

        # determine width of graph
        date_offset = 80
        page_width = date_offset + total_width
        # determine height of graph
        page_height = days * _SQUARE_SIZE

        img = Image.new("RGBA", (page_width, page_height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        layer = Image.new("RGBA", (page_width, page_height), (255, 255, 255, 0))
        drawtop = ImageDraw.Draw(layer)

        draw = self._write_dates((0, page_height), start, days, draw)

        # draw individual squares
        map = []
        x, y = date_offset, page_height
        draw.rectangle([x, y, x + total_width - 1, y - page_height + 1], fill=(229, 229, 229, 255))
        idate = start
        for i in range(days):
            x = date_offset
            for j, res in enumerate(resources):
                statement = '''select sum(value) from narcissus_data where resource = "%s"
                    and dtime >= %s and dtime < %s''' % (res, idate, idate + MICROSECONDS_DAY)
                cursor.execute(statement)
                total_value = cursor.fetchone()[0]
                if total_value:
                    y = page_height - self._date_y(start, idate)
                    score = self._get_score(res, total_value)
                    drawtop.rectangle([x, y, x + widths[j] - 1, y - _SQUARE_SIZE + 1],
                        fill=(_RED[j], _GREEN[j], _BLUE[j], score * 0.25 * 255))
                    # add info for the template to render an image map
                    idx = '%s_%s' % (res, idate)
                    href = '%s/details?resource=%s&date=%s'\
                        % (req.base_url, res, idate)
                    item = {}
                    item['href'] = href
                    item['x1'] = x
                    item['y1'] = y - _SQUARE_SIZE
                    item['x2'] = x + widths[j]
                    item['y2'] = y
                    map.append(item)
                x += widths[j]
            idate += MICROSECONDS_DAY
        params['mapItems'] = map

        img = Image.composite(layer, img, layer)
        params['vis'] = self._cache_image(req, params, img, 'vis')

    def _draw_ticket(self, req, params):
        # Draw image and generate data for image map for ticket view
        start, end, days = self._get_dates(params)
        members = self._settings.members
        resources = self._settings.resources
        cursor = self.db.cursor()
        
        # ids are required for mapping members to their colours
        midx = {}
        for i, m in enumerate(members):
            midx[m] = i

        # group tickets according to the owner
        mem_tickets, owned_tickets = {}, 0
        for mem in members:
            statement = '''select id from ticket where owner = "%s" and not 
                (status = "closed" and changetime <= %s) and not time > %s'''\
                % (mem, start, end)
            cursor.execute(statement)
            mem_tickets[mem] = [t[0] for t in cursor]
            owned_tickets += len(mem_tickets[mem])

        if owned_tickets == 0:
            params['msg'] = 'There are no tickets to visualise in the selected time period'
            return

        # ticket size is relative to number of tickets and "screen size"
        ticket_width = self._bounded(_TICKET_MIN, _SCREEN_SPACE / owned_tickets, _TICKET_MAX)

        date_offset, bar_gap, name_offset = 80, 20, 30
        # determine width of graph
        page_width = date_offset + (owned_tickets * ticket_width) + (len(members) * bar_gap)
        # determine height of graph
        page_height = name_offset + (days * _SQUARE_SIZE)

        img = Image.new("RGBA", (page_width, page_height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)

        draw = self._write_dates((0, page_height), start, days, draw)
        
        # draw individual tickets
        map = []
        memx = date_offset
        colh = days * _SQUARE_SIZE
        for i, mem in enumerate(members):
            x, y = memx, page_height
            colw = len(mem_tickets[mem]) * ticket_width
            draw.rectangle([x, y, x + colw - 1, y - colh + 1], fill=(229, 229, 229, 255))
            for j, tid in enumerate(mem_tickets[mem]):
                ticket = Ticket(self.env, tid)
                tcreated = self._to_microseconds(ticket.time_created.date())

                starty = page_height - self._date_y(start, tcreated)
                x = memx + (j * ticket_width)

                # determine the colour index for the reported circle
                reporter = ticket['reporter']
                if reporter not in midx:
                    continue #reporter not configured in Narcissus settings, so don't show ticket
                cidx = midx[reporter]

                dots = [(starty, cidx)]

                # create the ticket lines: last change starts as ticket open,
                # line starts as thin, colour starts as black
                draw_from = draw_to = tcreated
                width = change_width = ticket_width / 4
                status = ticket['status']
                for dtime, _, field, _, newvalue, _ in ticket.get_changelog():
                    dtime = self._to_microseconds(dtime)
                    if dtime <= end:
                        dot = None
                        ttype = field
                        if ttype == 'status':
                            ttype = newvalue
                        if ttype == 'assigned':
                            draw_to = dtime
                            change_width = ticket_width / 2
                            status = 'assigned'
                        elif ttype == 'resolution':
                            draw_to = dtime
                            dot = midx[ticket['reporter']] + 1
                            status = 'closed'
                        elif ttype == 'reopened':
                            draw_to = dtime
                            change_width = ticket_width / 4
                            dot = midx[ticket['reporter']] + 1
                            status = 'new'
                        if draw_to > draw_from:
                            draw_days = self._date_days(draw_to - draw_from)
                            y = page_height - self._date_y(start, draw_from) - (_SQUARE_SIZE / 2)
                            draw.line([x + (ticket_width / 2), y,
                                x + (ticket_width / 2), y - draw_days * _SQUARE_SIZE],
                                fill=(128, 128, 128, 255), width=width)
                        if dot:
                            y = page_height - self._date_y(start, draw_to)
                            dots.append((y, dot - 1))
                        draw_from = draw_to
                        width = change_width
                if status != 'closed' or draw_to > end:
                    draw_days = self._date_days(end - draw_from)
                    y = page_height - self._date_y(start, draw_from) - (_SQUARE_SIZE / 2)
                    draw.line([x + (ticket_width / 2), y, x + (ticket_width / 2),
                        y - (draw_days * _SQUARE_SIZE + (_SQUARE_SIZE / 2))], 
                        fill=(128, 128, 128, 255), width=width)
                for dot in dots:
                    y, i = dot[0] - (_SQUARE_SIZE / 2), dot[1]
                    draw.ellipse([x, y - ticket_width, x + ticket_width, y],
                        fill=(_RED[i%len(_RED)], _GREEN[i%len(_GREEN)], _BLUE[i%len(_BLUE)], 255))
    
                # default length if there haven't been any changes to the ticket yet
                last_change = end
                if ticket['status'] == 'closed':
                    for dtime, _, _, _, _, _ in ticket.get_changelog():
                        dtime = self._to_microseconds(dtime)
                        if dtime <= end:
                            last_change = dtime
                ticket_length = self._date_days(last_change - tcreated) + 1

                # add info for the template to render an image map
                idx = 'ticket_%s' % (tid)
                href = '%s/details?tid=%s' % (req.base_url, tid)
                item = {}
                item['href'] = href
                item['x1'] = x
                item['y1'] = starty - (ticket_length * _SQUARE_SIZE)
                item['x2'] = x + ticket_width
                item['y2'] = starty
                map.append(item)

            # print member name
            x, y = memx + 10, name_offset * 0.4
            draw.text((x, y), mem, fill=(0, 0, 0, 255), font=self._ttf)
            
            # increment the horizontal point for the next member
            memx += colw + bar_gap

        params['mapItems'] = map
        params['vis'] = self._cache_image(req, params, img, 'vis')

    def _write_dates(self, start_pos, idate, days, draw):
        # Write dates along left of image
        x, y = start_pos
        for i in range(days):
            draw.text((x, y - _SQUARE_SIZE/1.5), str(self._from_db_time(idate)), fill=(0, 0, 0, 255), font=self._ttf)
            y -= _SQUARE_SIZE
            idate += MICROSECONDS_DAY
        return draw

    # Utility methods
    def _cache_image(self, req, params, img, name):
        # Cache image according to configuration in trac.ini (see _load_config)
        # Parts of this function are modified from the graphviz plugin, (c) Peter Kropf
        trouble, msg = self._load_config()
        if trouble:
            params['error'] = msg.getvalue()
            return None

        buf = StringIO()
        
        # Use hash to determine image name for cache
        view = req.args.get('view', 'group')
        sha_text = '%s%s%s' % (view, name, time.time())
        sha_key = hashlib.sha1(sha_text).hexdigest()

        img_name = '%s.png' % (sha_key)
        img_path = os.path.join(self.cache_dir, img_name)

        # Create image if not in cache
        if not os.path.exists(img_path):
            self._clean_cache()
        
        img.save(img_path, 'PNG')
        d = {}
        d['href'] = '%s%s?img=%s' % (req.base_url, req.path_info, img_name)
        d['width'] = img.size[0]
        d['height'] = img.size[1]
        return d

    def _load_config(self):
        # Load the narcissus trac.ini configuration into object instance variables.
        # The code in this function is modified from the graphviz plugin, (c) Peter Kropf
        buf = StringIO()
        trouble = False
        self.exe_suffix = ''
        if sys.platform == 'win32':
            self.exe_suffix = '.exe'

        if 'narcissus' not in self.config.sections():
            msg = 'The narcissus section was not found in the trac configuration file.'
            buf.write(escape(msg))
            self.log.error(msg)
            trouble = True
        else:
            # check for the cache_dir entry
            self.cache_dir = self.config.get('narcissus', 'cache_dir')
            if not self.cache_dir:
                msg = 'The narcissus section is missing the cache_dir field.'
                buf.write(escape(msg))
                self.log.error(msg)
                trouble = True
            else:
                if not os.path.exists(self.cache_dir):
                    msg = 'The cache_dir is set to %s but that path does not exist.'\
                        % self.cache_dir
                    buf.write(escape(msg))
                    self.log.error(msg)
                    trouble = True

            # check for the cmd_path entry
            self.cmd_path = None
            if sys.platform in _CMD_PATHS:
                self.cmd_path = _CMD_PATHS[sys.platform]
            self.cmd_path = self.config.get('narcissus', 'cmd_path', self.cmd_path)
            if not self.cmd_path:
                msg = '''The narcissus section is missing the cmd_path field and
                    there is no default for %s.''' % sys.platform
                buf.write(escape(msg))
                self.log.error(msg)
                trouble = True
            elif not os.path.exists(self.cmd_path):
                msg = 'The cmd_path is set to %s but that path does not exist.' % self.cmd_path
                buf.write(escape(msg))
                self.log.error(msg)
                trouble = True

            # check if we should run the cache manager
            self.cache_manager = self._boolean(self.config.get('narcissus', 'cache_manager', False))
            if self.cache_manager:
                self.cache_max_size  = int(self.config.get('narcissus', 'cache_max_size',  10000000))
                self.cache_min_size  = int(self.config.get('narcissus', 'cache_min_size',  5000000))
                self.cache_max_count = int(self.config.get('narcissus', 'cache_max_count', 2000))
                self.cache_min_count = int(self.config.get('narcissus', 'cache_min_count', 1500))

        return trouble, buf

    def _clean_cache(self):
        """This function is taken from the graphviz plugin, (c) Peter Kropf

        The cache manager (clean_cache) is an attempt at keeping the
        cache directory under control. When the cache manager
        determines that it should clean up the cache, it will delete
        files based on the file access time. The files that were least
        accessed will be deleted first.

        The graphviz section of the trac configuration file should
        have an entry called cache_manager to enable the cache
        cleaning code. If it does, then the cache_max_size,
        cache_min_size, cache_max_count and cache_min_count entries
        must also be there."""

        if self.cache_manager:
            # os.stat gives back a tuple with: st_mode(0), st_ino(1),
            # st_dev(2), st_nlink(3), st_uid(4), st_gid(5),
            # st_size(6), st_atime(7), st_mtime(8), st_ctime(9)

            entry_list = {}
            atime_list = {}
            size_list = {}
            count = 0
            size = 0

            for name in os.listdir(self.cache_dir):
                entry_list[name] = os.stat(os.path.join(self.cache_dir, name))

                atime_list.setdefault(entry_list[name][7], []).append(name)
                count = count + 1

                size_list.setdefault(entry_list[name][6], []).append(name)
                size = size + entry_list[name][6]

            atime_keys = atime_list.keys()
            atime_keys.sort()

            # In the spirit of keeping the code fairly simple, the
            # clearing out of files from the cache directory may
            # result in the count dropping below cache_min_count if
            # multiple entries are have the same last access
            # time. Same for cache_min_size.
            if count > self.cache_max_count or size > self.cache_max_size:
                while len(atime_keys) and (self.cache_min_count < count or self.cache_min_size < size):
                    key = atime_keys.pop(0)
                    for file in atime_list[key]:
                        os.unlink(os.path.join(self.cache_dir, file))
                        count = count - 1
                        size = size - entry_list[file][6]
        else:
            pass

    def _get_font(self):
        # Load the narcissus trac.ini font configuration into an instance variable
        buf = StringIO()
        trouble = False

        if 'narcissus' not in self.config.sections():
            msg = 'The narcissus section was not found in the trac configuration file.'
            buf.write(escape(msg))
            self.log.error(msg)
            trouble = True
        else:
            # check for the ttf_path entry
            self._ttf_path = self.config.get('narcissus', 'ttf_path')
            if not self._ttf_path:
                self._ttf = None # PIL will use default system font
                return None, None
            if not self._ttf_path[-4:].lower() == '.ttf':
                msg = 'The ttf_path is set to %s which is not a truetype font file.'\
                    % self._ttf_path
                buf.write(escape(msg))
                self.log.error(msg)
                trouble = True
            if not os.path.exists(self._ttf_path):
                msg = 'The ttf_path is set to %s but that path does not exist.'\
                    % self._ttf_path
                buf.write(escape(msg))
                self.log.error(msg)
                trouble = True
            self._ttf = ImageFont.truetype(self._ttf_path, 12)
        return trouble, buf

    # Extra helper functions
    def _boolean(self, value):
        # This function is taken from the graphviz plugin, (c) Peter Kropf
        # (in turn almost directly from trac.config in the 0.10 line...)
        if isinstance(value, basestring):
            value = value.lower() in _TRUE_VALUES
        return bool(value)
    
    def _get_dates(self, params):
        # Determine the dates and number of days to be visualised
        days = int(params['date_daysback']) + 1 # inclusive of start and end dates
        #end = self._to_date(float(params['date_end']))
        #start = end - datetime.timedelta(days=(days - 1))
        end = int(float(params['date_end']) * MICROSECONDS_SECOND)
        start = end - (days * MICROSECONDS_DAY)
        return start, end, days

    def _to_date(self, timestamp):
        # Given a timestamp, return the datetime object
        return datetime.date.fromtimestamp(timestamp)

    def _from_db_time(self, timestamp):
        # Given a timestamp from the datbase, return a corressponding datetime object
        return datetime.date.fromtimestamp(timestamp / MICROSECONDS_SECOND);
    
    def _date_y(self, start, idate):
        # Determine the y potision relative the the start date
        #return (idate - start).days * _SQUARE_SIZE
        #return datetime.timedelta(microseconds=(idate - start)).days * _SQUARE_SIZE
        return self._date_days(idate-start) * _SQUARE_SIZE

    def _date_days(self, idate):
        return datetime.timedelta(microseconds=idate).days
    
    def _to_microseconds(self, idate):
        return time.mktime(idate.timetuple()) * MICROSECONDS_SECOND

    def _is_binary(self, data):
        # Detect binary content by checking the first thousand bytes for zeroes.
        # Operate on either `str` or `unicode` strings.
        return '\0' in data[:1000]

    def _edit_newlines(self, changes):
        # Return the number of new lines added to an edited text item.
        addedlines = 0
        for blocks in changes:
            for block in blocks:
                t = block['type']
                outlines = block['changed']['lines']
                lout = len(outlines)
                if t == 'add':
                    addedlines += lout
        return addedlines

    def _svn_add_newlines(self, repos, path, rev):
        # Return the number of new lines added to a repository add.
        node = repos.get_node(path, str(rev))
        if not node or node.isdir:
            return 0
        content = node.get_content().read()
        if self._is_binary(content):
             return 0 # ideally will provide score for binary contributions
        addedlines = len(content.splitlines())
        return addedlines or 0

    def _my_diff(self, old_content, new_content):
        # Determine the difference between two text items.
        if old_content == new_content:
            return None
        try:
            return diff_blocks(old_content.splitlines(),
                               new_content.splitlines(),
                               0, tabwidth=8,
                               ignore_blank_lines=True,
                               ignore_case=True,
                               ignore_space_changes=True)
        except UnicodeDecodeError:
            old_content = unicode(old_content, "iso-8859-1")
            new_content = unicode(new_content, "iso-8859-1")
            return diff_blocks(old_content.splitlines(),
                               new_content.splitlines(),
                               0, tabwidth=8,
                               ignore_blank_lines=True,
                               ignore_case=True,
                               ignore_space_changes=True)

    def _my_svn_diff(self, repos, args):
        # Determine the difference between repository versions.
        old_node = repos.get_node(args["old_path"], str(args["old_rev"]))
        new_node = repos.get_node(args["new_path"], str(args["new_rev"]))
        if new_node.isdir:
            return None
        old_content = old_node.get_content().read()
        if self._is_binary(old_content):
            return None
        new_content = new_node.get_content().read()
        if self._is_binary(new_content):
            return None    
        return self._my_diff(old_content, new_content)

    def _get_score(self, resource, value):
        # Function for discretising value to score of 0-4, according to resource
        bounds = self._settings.bounds[resource]
        value = int(value)
        if value is 0: return 0
        elif value <= bounds[0]: return 1
        elif value <= bounds[1]: return 2
        elif value <= bounds[2]: return 3
        elif value > bounds[2]: return 4

    def _bounded(self, a, v, b):
        # Return v -- no less than a and no greater than b
        if v < a: return a
        elif v > b: return b
        return v

    def _decode_string(self, v):
        try:
            return v.decode('utf-8')
        except UnicodeDecodeError:
            return v
        except UnicodeEncodeError:
            return v

