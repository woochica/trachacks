# -*- encoding: UTF-8 -*-
'''
Created on 28 oct. 2010

@author: thierry
'''
###############################################################################
##
##             O U T    O F    T H E    B O X    T A S K
##
###############################################################################
from time import  time, localtime
from trac.ticket.model import Ticket 
from trac.core import Component, implements
from trac.notification import NotifyEmail
from trac.web.chrome import ITemplateProvider
from traccron.api import ICronTask
from traccron.core import CronConfig

class HeartBeatTask(Component,ICronTask):
    """
    This is a simple task for testing purpose.
    It only write a trace in log at debug level
    """
    
    implements(ICronTask)
    
    def wake_up(self, *args):
        if len(args) > 0:
            for arg in args:
                self.env.log.debug("Heart beat: " + arg)
        else:
            self.env.log.debug("Heart beat: boom boom !!!")
    
    def getId(self):
        return "heart_beat"
    
    def getDescription(self):
        return self.__doc__
        

class SleepingTicketReminderTask(Component, ICronTask, ITemplateProvider):
    """
    Remind user about sleeping ticket they are assigned to.
    """
       
    implements(ICronTask, ITemplateProvider)
    
    def get_htdocs_dirs(self):
        return []


    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    
    def wake_up(self, *args):
        delay = 3        
        if len(args) > 0:
            delay = int(args[0])
        
        
        class SleepingTicketNotification(NotifyEmail):
            
            template_name  = "sleeping_ticket_template.txt"
            
            def __init__(self, env):
                NotifyEmail.__init__(self, env)

            def get_recipients(self, owner):
                return ([owner],[])

                
            
            def remind(self, tiketsByOwner):
                """
                Send a digest mail to ticket owner to remind him of those
                sleeping tickets
                """
                for owner in tiketsByOwner.keys():  
                    # prepare the data for the email content generation                      
                    self.data.update({
                                      "ticket_count": len(tiketsByOwner[owner]),
                                      "delay": delay
                                      })                                          
                    NotifyEmail.notify(self, owner, "Sleeping ticket notification")

            def send(self, torcpts, ccrcpts):
                return NotifyEmail.send(self, torcpts, ccrcpts)

            
        class OrphanedTicketNotification(NotifyEmail):
            
            template_name  = "orphaned_ticket_template.txt"
            
            def __init__(self, env):
                NotifyEmail.__init__(self, env)
                
            def get_recipients(self, reporter):
                return ([reporter],[])
            
            def remind(self, tiketsByReporter):
                """
                Send a digest mail to the reporter to remind them
                of those orphaned tickets
                """
                for reporter in tiketsByReporter.keys():  
                    # prepare the data for the email content generation                      
                    self.data.update({
                                      "ticket_count": len(tiketsByReporter[owner]),
                                      "delay": delay
                                      })                                          
                    NotifyEmail.notify(self, reporter, "orphaned ticket notification")


            def send(self, torcpts, ccrcpts):
                return NotifyEmail.send(self, torcpts, ccrcpts)            
            
                                
        # look for ticket assigned but not touched since more that the delay       
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        # assigned ticket
        cursor.execute("""
                SELECT t.id , t.owner  FROM ticket t, ticket_change tc                        
                WHERE  t.id = tc.ticket  
                AND    t.status in ('new','assigned','accepted')
                AND    (SELECT MAX(tc2.time) FROM ticket_change tc2 WHERE tc2.ticket=tc.ticket)  < %s GROUP BY t.id
            """, (time() - delay * 24 * 60 * 60,) )
        dico = {}
        for ticket, owner in cursor:
            self.env.log.info("warning ticket %d assigned to %s but is inactive since more than %d day" % (ticket, owner, delay))
            if dico.has_key(owner):
                dico[owner].append(ticket)
            else:
                dico[owner] = [ticket]
        SleepingTicketNotification(self.env).remind(dico)
        # orphaned ticket
        cursor.execute("""
               SELECT t.id, t.reporter  FROM  ticket t
               WHERE  t.id not in (select tc.ticket FROM ticket_change tc WHERE tc.ticket=t.id)
               AND t.time < %s AND t.status = 'new'
            """, (time() - delay * 24 * 60 * 60,) )
        dico = {}
        for ticket, reporter in cursor:
            self.env.log.info("warning ticket %d is new but orphaned" % (ticket,))
            if dico.has_key(reporter):
                dico[reporter].append(ticket)
            else:
                dico[reporter] = [ticket]
        OrphanedTicketNotification(self.env).remind(dico)
    
    def getId(self):
        return "sleeping_ticket"
    
    def getDescription(self):
        return self.__doc__
    


class UnreachableMilestoneTask(Component, ICronTask, ITemplateProvider):
    """
    Send notification about near milestone with opened ticked
    """
       
    implements(ICronTask, ITemplateProvider)
       
    def __init__(self):
        self.cronconf = CronConfig(self.env)
    
    def get_htdocs_dirs(self):
        return []


    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    


    def wake_up(self, *args):
        delay = 3        
        if len(args) > 0:
            delay = int(args[0])
        
        class BaseTicketNotification(NotifyEmail):
            
            def __init__(self, env, milestone):
                NotifyEmail.__init__(self, env)
                self.milestone = milestone
            
            def populate_unreachable_tickets_data(self, tickets):
                self.data['milestone'] = tickets[0]['milestone'] # we are not called if there is no tickets
                due_date = localtime(tickets[0]['due'])
                self.data['due_date'] = "%d-%d-%d" % (due_date.tm_mon, due_date.tm_mday, due_date.tm_year)
                tickets_list = ""
                for ticket in tickets:
                    tickets_list += ticket['summary'] + "\n"
                    tickets_list += self.env.abs_href.ticket(ticket['ticket']) + "\n"
                    tickets_list += "\n"
        
                self.data['tickets_list'] = tickets_list


        class ReporterOpenedTicketNotification(BaseTicketNotification):
            """
            Notify reporter about an opened ticket in
            a near milestone            
            """            
            template_name  = "opened_ticket_for_reporter_template.txt"
            
            def __init__(self, env, milestone):
                BaseTicketNotification.__init__(self, env, milestone)
                
              

            def get_recipients(self, reporter):                
                return ([reporter],[])

                
            
            def notify_opened_ticket(self, reporter, tickets):
                """
                Send a digest mail to ticket owner and reporter
                about ticket still opened 
                """
                
                self.populate_unreachable_tickets_data(tickets)                           
                NotifyEmail.notify(self, reporter, "Milestone %s with still opened ticket" % self.milestone)

            def send(self, torcpts, ccrcpts):
                return NotifyEmail.send(self, torcpts, ccrcpts)
            
            
        class OwnerOpenedTicketNotification(BaseTicketNotification):
            """
            Notify owner about an opened ticket in
            a near milestone            
            """
            template_name  = "opened_ticket_for_owner_template.txt"
            
            def __init__(self, env, milestone):
                BaseTicketNotification.__init__(self, env, milestone)
              

            def get_recipients(self, owner):                
                return ([owner],[])

                
            
            def notify_opened_ticket(self, owner, tickets):
                """
                Send a digest mail to ticket owner
                about ticket still opened 
                """
                
                self.populate_unreachable_tickets_data(tickets)                           
                NotifyEmail.notify(self, owner, "Milestone %s still has opened ticket" % self.milestone)

            def send(self, torcpts, ccrcpts):
                return NotifyEmail.send(self, torcpts, ccrcpts)

            
        class UnreachableMilestoneNotification(BaseTicketNotification):
            """
            Notify the specified person (ex: admin, release manager) that a milestone
            is about to closed but there still are opened ticket 
            """
            
            template_name  = "unreachable_milestone_template.txt"
            
            def __init__(self, env, milestone):
                BaseTicketNotification.__init__(self, env, milestone)
                self.cronconf = CronConfig(self.env)                
                
            def get_recipients(self, milestone):
                reclist = self.cronconf.get_unreachable_milestone_task_recipient_list()
                return (reclist,[])
            
            def notify_unreachable_milestone(self, tickets):
                """
                Send a digest mail listing all tickets still opened in the milestone
                """
                self.populate_unreachable_tickets_data(tickets)
               
                NotifyEmail.notify(self, self.milestone, "Milestone %s still has opened ticket" % self.milestone)


            def send(self, torcpts, ccrcpts):
                return NotifyEmail.send(self, torcpts, ccrcpts)            
            
                                
        # look opened ticket in near milestone
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        # select ticket whom milestone are due in less than specified delay
        cursor.execute("""
                SELECT t.id , t.owner, t.reporter, t.milestone, t.summary, m.due  FROM ticket t, milestone m                        
                WHERE  t.milestone = m.name  
                AND    m.due < %s                
            """, (time() + delay * 24 * 60 * 60,) )
        dico = {}
        dico_reporter = {}
        dico_owner = {}
        for ticket, owner, reporter, milestone, summary, due in cursor:
            self.env.log.info("warning ticket %d will probably miss its milestone %s" % (ticket, milestone))
            ticket_data = {'ticket':ticket,
                           'owner': owner,
                           'reporter' : reporter,
                           'milestone' : milestone,
                           'summary': summary,
                           'due' : due
                         }
            if dico.has_key(milestone):
                dico[milestone].append(ticket_data)
            else:
                dico[milestone] = [ticket_data]
                
            if dico_owner.has_key(owner):
                if dico_owner[owner].has_key(milestone):
                    dico_owner[owner][milestone].append(ticket_data)
                else:
                    dico_owner[owner][milestone] = [ticket_data]
            else:
                dico_owner[owner] = {milestone:[ticket_data]}
                
            if dico_reporter.has_key(reporter):
                if dico_reporter[reporter].has_key(milestone):
                    dico_reporter[reporter][milestone].append(ticket_data)
                else:
                    dico_reporter[reporter][milestone] = [ticket_data]
            else:
                dico_reporter[reporter] = {milestone:[ticket_data]}
            
        for milestone in dico.keys():
            # send notification for each milestone
            UnreachableMilestoneNotification(self.env, milestone).notify_unreachable_milestone(dico[milestone])
        for owner in dico_owner.keys():
            # for this owner
            _dico_owner = dico_owner[owner]
            for milestone in _dico_owner.keys(): 
                OwnerOpenedTicketNotification(self.env, milestone).notify_opened_ticket(owner, _dico_owner[milestone] )
        for reporter in dico_reporter.keys():
            _dico_reporter = dico_reporter[reporter]
            for milestone in _dico_reporter.keys():
                ReporterOpenedTicketNotification(self.env, milestone).notify_opened_ticket(reporter, _dico_reporter[milestone])
                    
    def getId(self):
        return self.cronconf.UNREACHABLE_MILESTONE_TASK_BASEKEY
    
    def getDescription(self):
        return self.__doc__
    

class AutoPostponeTask(Component,ICronTask):
    """
    Scan closed milestone for still opened ticket then posptone those tickets
    to the next milestone
    """
    
    implements(ICronTask)
    
    

    def wake_up(self, *args):
        db = self.env.get_db_cnx()        
        cursor = db.cursor()
        # find still opened more recent milestone
        # select ticket whom milestone are due in less than specified delay
        cursor.execute("""
                SELECT m.name  FROM milestone m                        
                WHERE  m.completed is NULL or m.completed = 0
                AND m.due not NULL and m.due > 0
                ORDER BY m.due ASC LIMIT 1            
            """ )
        next_milestone = None
        for name, in cursor:
            next_milestone = name            
                
        # select ticket whom milestone are due in less than specified delay
        cursor.execute("""
                SELECT t.id , t.milestone  FROM ticket t, milestone m                        
                WHERE t.status != 'closed'
                AND    t.milestone = m.name  
                AND    m.completed not NULL and m.completed > 0            
            """ )        
        if next_milestone:          
            for id, milestone in cursor:
                mess = "ticket %s is opened in closed milestone %s. Should postpone this ticket to %s" % (id, milestone, next_milestone)
                self.env.log.debug(mess)
                ticket = Ticket(self.env, id)
                ticket.populate({'milestone':next_milestone})
                ticket.save_changes(self.getId(),mess)
        else:
            self.env.log.debug("No opened milestone found. Cannot postpone tickets")
            


    def getId(self):
        return "auto_postpone"


    def getDescription(self):
        return self.__doc__

    
