# -*- coding: utf-8 -*-
'''for KSTracMileMixView
    init all relational var
'''

Settings = {
    'rootpath':'/tracs/retracs'
    ,'projname':'trac1'
    ,'dbname':'db/trac.db'
    ,'ticketurl':'http://trac.example.com/trac1/ticket'
    ,'reporturl':'http://trac.example.com/trac1/report'
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

