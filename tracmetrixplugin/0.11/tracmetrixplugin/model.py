import sys
from datetime import timedelta, datetime
from trac.core import *
from trac.ticket import Ticket, model
from trac.util.datefmt import utc
from trac.ticket.roadmap import ITicketGroupStatsProvider, TicketGroupStats


class ProgressTicketGroupStatsProvider(Component):
    implements(ITicketGroupStatsProvider)

    def get_ticket_group_stats(self, ticket_ids):
        
        # ticket_ids is a list of ticket id as number.
        total_cnt = len(ticket_ids)
        if total_cnt:
            cursor = self.env.get_db_cnx().cursor() # get database connection
            str_ids = [str(x) for x in sorted(ticket_ids)] # create list of ticket id as string
            
            
            closed_cnt = cursor.execute("SELECT count(1) FROM ticket "
                                        "WHERE status = 'closed' AND id IN "
                                        "(%s)" % ",".join(str_ids)) # execute query and get cursor obj.
            closed_cnt = 0
            for cnt, in cursor:
                closed_cnt = cnt
                
            active_cnt = cursor.execute("SELECT count(1) FROM ticket "
                                        "WHERE status IN ('new', 'reopened') "
                                        "AND id IN (%s)" % ",".join(str_ids)) # execute query and get cursor obj.
            active_cnt = 0
            for cnt, in cursor:
                active_cnt = cnt
                
        else:
            closed_cnt = 0
            active_cnt = 0

        inprogress_cnt = total_cnt - ( active_cnt + closed_cnt)

        stat = TicketGroupStats('ticket status', 'ticket')
        stat.add_interval('closed', closed_cnt,
                          {'status': 'closed', 'group': 'resolution'},
                          'closed', True)
        stat.add_interval('inprogress', inprogress_cnt,
                          {'status': ['accepted', 'assigned']},
                          'inprogress', False)
        stat.add_interval('new', active_cnt,
                          {'status': ['new', 'reopened']},
                          'new', False)
                          
        stat.refresh_calcs()
        return stat


class TicketTypeGroupStatsProvider(Component):
    implements(ITicketGroupStatsProvider)

    def get_ticket_group_stats(self, ticket_ids):
        
        # ticket_ids is a list of ticket id as number.
        total_cnt = len(ticket_ids)
        if total_cnt:
            str_ids = [str(x) for x in sorted(ticket_ids)] # create list of ticket id as string
            cursor = self.env.get_db_cnx().cursor()  # get database connection    
            
            type_count = [] # list of dictionary with key name and count
            
            for type in model.Type.select(self.env):
            
                count = cursor.execute("SELECT count(1) FROM ticket "
                                        "WHERE type = '%s' AND id IN "
                                        "(%s)" % (type.name, ",".join(str_ids))) # execute query and get cursor obj.
                count = 0
                for cnt, in cursor:
                    count = cnt

                if count > 0:
                    type_count.append({'name':type.name,'count':count})

        
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
    
    def __init__(self, env, tkt_ids):

        self.env = env
        self.tickets = tkt_ids
        self.num_tickets = len(tkt_ids)
        self.ticket_metrics = [TicketMetrics(env,id) for id in tkt_ids]
    
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
        stats = DescriptiveStats(data)
        return stats
    
    def get_closed_time_stats(self):
        data = [tkt_metrics.closed_time for tkt_metrics in self.ticket_metrics]      
        stats = DescriptiveStats(data)
        return stats
    
    
class TicketMetrics(object):
    
    def __init__(self, env, tkt_id):
    
        self.id = tkt_id
    
        self.lead_time = 0
        self.closed_time = 0
        self.num_comment = 0
        self.num_closed = 0
        self.num_milestone = 0        
    
        #get ticket object
        ticket = Ticket(env, tkt_id)
    
        self.__collect_history_data(ticket)
    
    def __inseconds(self, duration):
        # convert timedelta object to interger value in seconds
        return duration.days*24*3600 + duration.seconds
        
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
                    self.lead_time = self.lead_time + self.__inseconds(t-previous_status_change)
                    
                elif newvalue == 'reopen':
                    self.closed_time = self.closed_time + self.__inseconds(t-previous_status_change)
                    
                else:
                    self.lead_time = self.lead_time + self.__inseconds(t-previous_status_change)
                
                previous_status = newvalue
                previous_status_change = t
            
            elif field == 'comment':
                if newvalue != '':
                    self.num_comment += 1
    
        # Claculate the ticket time up to current.
        if previous_status == 'closed':
            self.closed_time = self.closed_time + self.__inseconds(datetime.now(utc)- previous_status_change)

        else:
            self.lead_time = self.lead_time + self.__inseconds(datetime.now(utc)- previous_status_change)

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