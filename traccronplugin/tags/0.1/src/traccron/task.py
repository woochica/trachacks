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
from time import  time
from trac.core import Component, implements
from trac.notification import NotifyEmail
from trac.web.chrome import ITemplateProvider
from traccron.api import ICronTask

class HeartBeatTask(Component,ICronTask):
    """
    This is a simple task for testing purpose.
    It only write a trace in log a debug level
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
    
