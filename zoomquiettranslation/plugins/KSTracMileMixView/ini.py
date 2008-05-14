# -*- coding: utf-8 -*-
'''for KSTracRelaTicket
    init all relational var
'''

Settings = {
    'rootpath':'/tracs/retracs'
    ,'projname':'KXEngine'
    ,'dbname':'db/trac.db'
    ,'ticketurl':'http://trac.rdev.kingsoft.net/KXEngine/ticket'
    ,'reporturl':'http://trac.rdev.kingsoft.net/KXEngine/report'
    ,'dumpath':'data'
    ,'logpath':'log'
    ,'expath':'exp'
    ,'tplpath':'tpl'
    ,'defont':'/usr/share/fonts/VeraSansYuanTi/VeraSansYuanTiMono-Regular.ttf'
    }

sqltrac={
        "allTickets":'''SELECT 
            id,type,time,changetime 
            ,component,severity,priority 
            ,owner,reporter 
            ,status,resolution,summary,milestone 
            FROM ticket ;'''
#        ,"allCustom":"SELECT * FROM `ticket_custom` ;"
#        ,"allDue":"SELECT * FROM `ticket_custom` WHERE name='duetime';"
        ,"timeMin":'''SELECT 
            min(time) 
            FROM ticket 
            WHERE milestone like "%s%%";'''
        ,"allDue":'''SELECT tc.ticket, tc.name, tc.value 
            FROM ticket_custom tc, ticket t 
            WHERE tc.ticket = t.id 
            and tc.name='duetime' 
            and t.milestone like "%s%%";'''
        ,"allMilestone":"SELECT milestone FROM `rt_template`;"
        ,"allTicketsOneDay":'''SELECT 
            id,type,time,changetime 
            ,component,severity,priority 
            ,owner,reporter 
            ,status,resolution,summary,milestone 
            FROM ticket 
            WHERE milestone like "%s%%";'''
        ,"currentStatus":'''SELECT 
            newvalue, max(time) 
            FROM ticket_change
            WHERE ticket = %d
            and field = "status"
            and time < %d
            ORDER BY time ;'''
        ,"createdStatus":'''SELECT 
            "new" 
            FROM ticket
            WHERE id = %d 
            and time < %d ;'''
}

#SELECT id, time, status 
#FROM ticket
#WHERE milestone like "WSS.m1.1%"
#ORDER BY time
#
#SELECT *
#FROM ticket_change
#WHERE milestone like "WSS.m1.1%"
#ORDER BY time
#
#
#SELECT 
#            status, id , time
#            FROM ticket
#            WHERE time < 1209848000
#and milestone like "WSS.m1.1%"


#SELECT tc.ticket, tc.newvalue, datetime(tc.time, 'unixepoch', 'localtime'), datetime(t.time, 'unixepoch', 'localtime'), tcu.value
#FROM ticket_change tc, ticket t, ticket_custom tcu
#WHERE tc.ticket = t.id and tcu.ticket = t.id
#and tcu.name = 'duetime' 
#and t.milestone like "WSS.m1.1%"
#and field='status'
#ORDER BY t.id, tc.time
