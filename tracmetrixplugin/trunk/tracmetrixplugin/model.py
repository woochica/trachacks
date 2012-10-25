# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Bhuricha Sethanadha <khundeen@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac-hacks.org/wiki/TracMetrixPlugin.
#
# Author: Bhuricha Sethanandha <khundeen@gmail.com>

import os

from datetime import timedelta
from bisect import bisect

from pylab import date2num, drange, num2date

from trac.core import *
from trac.ticket import Ticket, model
from trac.ticket.roadmap import ITicketGroupStatsProvider, TicketGroupStats
from trac.util.datefmt import utc, to_timestamp, to_datetime, format_date

# set HOME environment variable to a directory the httpd server can write to
# (matplotlib needs this)
os.environ[ 'HOME' ] = '/tmp/'

class ProgressTicketGroupStatsProvider(Component):
    implements(ITicketGroupStatsProvider)

    def get_ticket_group_stats(self, ticket_ids):

        # ticket_ids is a list of ticket id as number.
        total_count = len(ticket_ids)
        status_count = {
            'closed': 0,
            'new': 0,
            'reopened': 0
        }

        if total_count:
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            str_ids = [str(x) for x in sorted(ticket_ids)]
            cursor.execute("""
                SELECT status, count(status) FROM ticket
                WHERE id IN (%s) GROUP BY status"""
                % ",".join(str_ids))

            for status, count in cursor.fetchall():
                status_count[status] = count

        inprogress_cnt = total_count - (status_count['new'] + \
            status_count['reopened'] + status_count['closed'])

        stat = TicketGroupStats('ticket status', 'ticket')
        stat.add_interval('closed', status_count['closed'],
                          {'status': 'closed', 'group': 'resolution'},
                          'closed', True)
        stat.add_interval('inprogress', inprogress_cnt,
                          {'status': ['accepted', 'assigned']},
                          'inprogress', False)
        stat.add_interval('new', status_count['new'] + status_count['reopened'],
                          {'status': ['new', 'reopened']},
                          'new', False)

        stat.refresh_calcs()
        return stat

    def get_ticket_resolution_group_stats(self, ticket_ids):
        # ticket_ids is a list of ticket ids with type int

        stat = TicketGroupStats('ticket resolution', 'ticket')

        if len(ticket_ids):
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            str_ids = [str(x) for x in sorted(ticket_ids)]

            cursor.execute("""
                SELECT resolution, count(resolution) FROM ticket
                WHERE status='closed' AND id IN (%s)"""
                % ",".join(str_ids))

            resolution_count = {}
            for resolution, count in cursor.fetchall():
                resolution_count[resolution] = count

            for key, value in resolution_count.iteritems():
                if key in ('fixed', 'completed'): # default ticket type 'defect'        
                    stat.add_interval(
                        {'resolution': key}, 'value', True)
                else:
                    stat.add_interval(key, value,
                        {'resolution': key}, 'waste', False)

        stat.refresh_calcs()
        return stat

    def get_ticket_type_group_stats(self, ticket_ids):

        # ticket_ids is a list of ticket id as number.
        total_cnt = len(ticket_ids)
        if total_cnt:

            db = self.env.get_db_cnx()
            cursor = db.cursor()

            type_count = [] # list of dictionary with key name and count

            for type in model.Type.select(self.env):

                count = cursor.execute("SELECT COUNT(*) FROM ticket "
                                        "WHERE type = %%s AND id IN (%s)"
                                        % (",".join(['%s'] * len(ticket_ids))), (type.name,) + tuple(ticket_ids))
                count = cursor.fetchone()[0]
                if count > 0:
                    type_count.append({'name':type.name, 'count':count})

        else:
            type_count = []

        stat = TicketGroupStats('ticket type', 'ticket')


        for type in type_count:

            if type['name'] != 'defect': # default ticket type 'defect'

                stat.add_interval(type['name'], type['count'],
                                  {'type': type['name']}, 'value', True)

            else:
                stat.add_interval(type['name'], type['count'],
                                  {'type': type['name']}, 'waste', False)

        stat.refresh_calcs()
        return stat

class TicketTypeGroupStatsProvider(Component):
    implements(ITicketGroupStatsProvider)

    def get_ticket_group_stats(self, ticket_ids):

        # ticket_ids is a list of ticket id as number.
        total_cnt = len(ticket_ids)
        if total_cnt:

            db = self.env.get_db_cnx()
            cursor = db.cursor()

            type_count = [] # list of dictionary with key name and count

            for type in model.Type.select(self.env):

                cursor.execute("SELECT COUNT(*) FROM ticket "
                               "WHERE type = %%s AND id IN (%s)"
                               % (",".join(['%s'] * len(ticket_ids))), (type.name,) + tuple(ticket_ids))
                count = cursor.fetchone()[0]
                if count > 0:
                    type_count.append({'name':type.name, 'count':count})

        else:
            type_count = []

        stat = TicketGroupStats('ticket type', 'ticket')


        for type in type_count:

            if type['name'] != 'defect': # default ticket type 'defect'

                stat.add_interval(type['name'], type['count'],
                                  {'type': type['name']}, 'value', True)

            else:
                stat.add_interval(type['name'], type['count'],
                                  {'type': type['name']}, 'waste', False)

        stat.refresh_calcs()
        return stat

class TicketGroupMetrics(object):

    def __init__(self, env, ticket_ids):

        self.env = env
        self.tickets = [Ticket(env, id) for id in ticket_ids]
        self.ticket_metrics = [TicketMetrics(env, t) for t in self.tickets]

    def get_num_comment_stats(self):

        data = [tkt_metrics.num_comment for tkt_metrics in self.ticket_metrics]
        stats = DescriptiveStats(data)
        return stats

    def get_num_closed_stats(self):

        data = [tkt_metrics.num_closed for tkt_metrics in self.ticket_metrics]
        stats = DescriptiveStats(data)
        return stats

    def get_num_milestone_stats(self):

        data = [tkt_metrics.num_milestone for tkt_metrics in self.ticket_metrics]
        stats = DescriptiveStats(data)
        return stats

    def get_frequency_metrics_stats(self):

        return {"Number of comments per ticket": self.get_num_comment_stats(),
                "Number of milestone changed per ticket": self.get_num_milestone_stats(),
                "Number of closed per ticket": self.get_num_closed_stats()}

    def get_duration_metrics_stats(self):

        return {"Lead time": self.get_lead_time_stats(),
                "Closed time": self.get_closed_time_stats()}

    def get_lead_time_stats(self):

        data = [tkt_metrics.lead_time for tkt_metrics in self.ticket_metrics]

        self.env.log.info(data)
        stats = DescriptiveStats(data)
        return stats

    def get_closed_time_stats(self):
        data = [tkt_metrics.closed_time for tkt_metrics in self.ticket_metrics]
        stats = DescriptiveStats(data)
        return stats

    def get_tickets_created_during(self, start_date, end_date):

        end_date = end_date.replace(hour=23, minute=59, second=59)

        tkt_ids = []

        for ticket in self.tickets:
            if start_date <= ticket.time_created <= end_date:
                tkt_ids.append(ticket.id)

        return tkt_ids

    def get_remaning_opened_ticket_on(self, end_date):

        end_date = end_date.replace(hour=23, minute=59, second=59)

        tkt_ids = []

        for ticket in self.tickets:

            # only consider the ticket that was created before the end date.
            if ticket.time_created <= end_date:

                if ticket.values['status'] == 'closed':

                    was_opened = True
                    # check change log to find the date when the ticket was closed.
                    for t, author, field, oldvalue, newvalue, permanent in ticket.get_changelog():
                        if field == 'status':

                            if newvalue == 'closed':
                                if t <= end_date:
                                    was_opened = False

                            else:
                                if t <= end_date:
                                    was_opened = True

                    if was_opened == True:
                        tkt_ids.append(ticket.id)

                # Assume that ticket that is not closed are opened
                else:
                    # only add the ticket that was created before the end date
                    if end_date >= ticket.time_created:
                        tkt_ids.append(ticket.id)

        return tkt_ids


    def get_tickets_closed_during(self, start_date, end_date):

        end_date = end_date.replace(hour=23, minute=59, second=59)

        tkt_ids = []

        for ticket in self.tickets:
            for t, author, field, oldvalue, newvalue, permanent in ticket.get_changelog():
                if field == 'status' and \
                   newvalue == 'closed' and \
                   start_date <= t <= end_date:

                   tkt_ids.append(ticket.id)

                   #only count the first closed
                   break

        return tkt_ids

    def get_bmi_monthly_stats(self, start_date, end_date):

        created_tickets = self.get_tickets_created_during(start_date, end_date)
        opened_tickets = self.get_remaning_opened_ticket_on(end_date)
        closed_tickets = self.get_tickets_closed_during(start_date, end_date)

        if opened_tickets == []:
            bmi = 0
        else:
            bmi = float(len(closed_tickets)) * 100 / float(len(opened_tickets))

        return ("%s/%s" % (start_date.month, start_date.year),
                created_tickets,
                opened_tickets,
                closed_tickets,
                bmi)

    def get_daily_backlog_history(self, start_date, end_date):
        """
            returns list of tuple (date,stats)
                date is date value in epoc time
                stats is dictionary of {'created':[], 'opened':[], 'closed':[]}
        """

        # this is array of date in numpy
        numdates = drange(start_date, end_date + timedelta(days=1), timedelta(days=1))

#        for date in numdates:
#            self.env.log.info(num2date(date))

        end_date = end_date.replace(hour=23, minute=59, second=59)


        # each key is the list of list of ticket.  The index of the list is corresponding
        # to the index of the date in numdates list.
        backlog_stats = {'created':[], 'opened':[], 'closed':[]}

        # initialize backlog_stats

        for date in numdates:
            for key in backlog_stats:
                backlog_stats[key].append([])

        # start by getting the list of opened ticket at the end of the start date.        
        backlog_stats['opened'][0] = self.get_remaning_opened_ticket_on(start_date)

        for ticket in self.tickets:

            # only consider the ticket that was created before end dates.
            if ticket.time_created <= end_date:

                # only track the ticket that create since start_date
                if ticket.time_created >= start_date:
                    # determine index
                    date = ticket.time_created.date()
                    #get index of day in the dates list
                    index = bisect(numdates, date2num(date)) - 1

                    # add ticket created ticket list
                    backlog_stats['created'][index].append(ticket.id)

                for t, author, field, oldvalue, newvalue, permanent in ticket.get_changelog():

                    # determine index
                    date = t.date()
                    #get index of day in the dates list
                    index = bisect(numdates, date2num(date)) - 1

                    if field == 'status' and start_date <= t <= end_date:

                        if newvalue == 'closed':
                            # add ticket created ticket list
                            backlog_stats['closed'][index].append(ticket.id)

                        elif newvalue == 'reopen':
                            backlog_stats['opened'][index].append(ticket.id)

        # update opened ticket list
        for idx, list in enumerate(backlog_stats['opened']):

            if idx > 0:

                # merge list of opened ticket from previous day
                list.extend(backlog_stats['opened'][idx - 1])

                # add created ticket to opened ticket list
                list.extend(backlog_stats['created'][idx])

                # remove closed ticket from opened ticket list.
                for id in backlog_stats['closed'][idx]:
                    try:
                        list.remove(id)
                    except ValueError, e:
                        pass


                list.sort()

#        for idx, numdate in enumerate(numdates):
#            self.env.log.info(num2date(numdate))
#            self.env.log.info(backlog_stats['created'][idx])
#            self.env.log.info(backlog_stats['opened'][idx])
#            self.env.log.info(backlog_stats['closed'][idx])                                                        

        return (numdates, backlog_stats)

    #This method return data point based on Yahoo JSArray format.      
    def get_daily_backlog_chart(self, backlog_history):

        numdates = backlog_history[0]
        backlog_stats = backlog_history[1]

        # create counted list.
        opened_tickets_dataset = [len(list) for list in backlog_stats['opened']]
        created_tickets_dataset = [len(list) for list in backlog_stats['created']]

        # need to add create and closed ticket for charting purpose. We want to show
        # closed tickets on top of opened ticket in bar chart.
        closed_tickets_dataset = []
        for i in range(len(created_tickets_dataset)):
            closed_tickets_dataset.append(created_tickets_dataset[i] + len(backlog_stats['closed'][i]))

        bmi_dataset = []
        for i in range(len(opened_tickets_dataset)):
            if opened_tickets_dataset[i] == 0:
                 bmi_dataset.append(0.0)
            else:
                bmi_dataset.append(float(closed_tickets_dataset[i]) * 100 / float(opened_tickets_dataset[i]))

#        for idx, numdate in enumerate(numdates):
#            self.env.log.info("%s: %s, %s, %s" % (num2date(numdate), 
#                                                    closed_tickets_dataset[idx],
#                                                    opened_tickets_dataset[idx],
#                                                    created_tickets_dataset[idx]))
        ds_daily_backlog = ''

        for idx, numdate in enumerate(numdates):
                    ds_daily_backlog = ds_daily_backlog + '{ date: "%s", opened: %d, closed: %d, created: %d}, ' \
                          % (format_date(num2date(numdate), tzinfo=utc), opened_tickets_dataset[idx], \
                             closed_tickets_dataset[idx], created_tickets_dataset[idx])

        return '[ ' + ds_daily_backlog + ' ];'
#        


class TicketMetrics(object):

    def __init__(self, env, ticket):

        #self.ticket = ticket

        self.lead_time = 0
        self.closed_time = 0
        self.num_comment = 0
        self.num_closed = 0
        self.num_milestone = 0

        self.__collect_history_data(ticket)

    def __inseconds(self, duration):
        # convert timedelta object to interger value in seconds
        return duration.days * 24 * 3600 + duration.seconds

    def __collect_history_data(self, ticket):

        previous_status = 'new'
        previous_status_change = ticket.time_created

        tkt_log = ticket.get_changelog()

        first_milestone_change = True

        for t, author, field, oldvalue, newvalue, permanent in tkt_log:

            if field == 'milestone' and first_milestone_change and oldvalue != '':
                self.num_milestone += 1;
                first_milestone_change = False

            elif field == 'milestone':
                if newvalue != '':
                    self.num_milestone += 1;

            elif field == 'status':

                if newvalue == 'closed':
                    self.num_closed += 1
                    self.lead_time = self.lead_time + self.__inseconds(t - previous_status_change)

                elif newvalue == 'reopen':
                    self.closed_time = self.closed_time + self.__inseconds(t - previous_status_change)

                else:
                    self.lead_time = self.lead_time + self.__inseconds(t - previous_status_change)

                previous_status = newvalue
                previous_status_change = t

            elif field == 'comment':
                if newvalue != '':
                    self.num_comment += 1

        # Calculate the ticket time up to current.
        if previous_status == 'closed':
            self.closed_time = self.closed_time + self.__inseconds(to_datetime(None, utc) - previous_status_change)

        else:
            self.lead_time = self.lead_time + self.__inseconds(to_datetime(None, utc) - previous_status_change)

    def get_all_metrics(self):
        return {'lead_time':self.lead_time,
                'closed_time':self.closed_time,
                'num_comment':self.num_comment,
                'num_closed':self.num_closed,
                'num_milestone':self.num_milestone}

class DescriptiveStats(object):

    def __init__(self, sequence):
        # sequence of numbers we will process
        # convert all items to floats for numerical processing        
        self.sequence = [float(item) for item in sequence]


    def sum(self):
        if len(self.sequence) < 1:
            return None
        else:
            return sum(self.sequence)

    def count(self):
        return len(self.sequence)

    def min(self):
        if len(self.sequence) < 1:
            return None
        else:
            return min(self.sequence)

    def max(self):
        if len(self.sequence) < 1:
            return None
        else:
            return max(self.sequence)

    def avg(self):
        if len(self.sequence) < 1:
            return None
        else:
            return sum(self.sequence) / len(self.sequence)

    def median(self):
        if len(self.sequence) < 1:
            return None
        else:
            self.sequence.sort()
            return self.sequence[len(self.sequence) // 2]

    def stdev(self):
        if len(self.sequence) < 1:
            return None
        else:
            avg = self.avg()
            sdsq = sum([(i - avg) ** 2 for i in self.sequence])
            stdev = (sdsq / (len(self.sequence) - 1 or 1)) ** .5
            return stdev

class ChangesetsStats:

    def __init__(self, env, start_date=None, stop_date=None):

        self.env = env

        self.start_date = start_date
        self.stop_date = stop_date
        self.first_rev = self.last_rev = None

        if start_date != None and stop_date != None:
            self.set_date_range(start_date, stop_date)

    def set_date_range(self, start_date, stop_date):

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        cursor.execute("SELECT rev, time, author FROM revision "
                       "WHERE time >= %s AND time < %s ORDER BY time",
                       (to_timestamp(start_date), to_timestamp(stop_date)))

        self.changesets = []
        for rev, time, author in cursor:
            self.changesets.append((rev, time, author))

        self.start_date = start_date
        self.stop_date = stop_date
        if not self.changesets:
            self.first_rev = self.last_rev = 0
        else:
            self.first_rev = self.changesets[0][0]
            self.last_rev = self.changesets[-1][0]

    def get_commit_by_date(self):

        numdates = drange(self.start_date, self.stop_date, timedelta(days=1))

        numcommits = [0 for i in numdates]

        for rev, time, author in self.changesets:

            date = to_datetime(time, utc).date()
            #get index of day in the dates list
            index = bisect(numdates, date2num(date)) - 1

            numcommits[index] += 1

        return (numdates, numcommits)

    # Return Yahoo JSARRAY format
    def get_commit_by_date_chart(self, commit_history):

        numdates = commit_history[0]
        numcommits = commit_history[1]

        ds_commits = ''

        for idx, numdate in enumerate(numdates):
                    ds_commits = ds_commits + '{ date: "%s", commits: %d}, ' \
                          % (format_date(num2date(numdate), tzinfo=utc), numcommits[idx])

        return '[ ' + ds_commits + ' ];'


