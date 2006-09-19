# IF YOU ADD A NEW SECTION OF REPORTS, You will need to make
# sure that section is also added to the all_reports hashtable
# near the bottom

#Please try to keep this clean"

billing_reports = [
        {
    "title":"Ticket Work Summary",
    "reportnumber":None,
    "version":3,
    "sql":"""
SELECT ticket as __group__,__style__, ticket, 
newvalue as [Hours-added], time as _time, strtime as [Time-Entered],
 _ord
FROM(
SELECT '' as __style__, author, t.id as ticket, newvalue,
 ticket_change.time as time,
 strftime('%m/%d/%Y %H:%M:%S', ticket_change.time, 'unixepoch', 'localtime') as strtime ,
 0  as _ord
FROM ticket_change
JOIN ticket t on t.id = ticket_change.ticket
LEFT JOIN ticket_custom as billable on billable.ticket = t.id 
  and billable.name = 'billable'
WHERE field = 'hours' and
  t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
    AND ticket_change.time >= $STARTDATE
    AND ticket_change.time < $ENDDATE

UNION 

SELECT 'background-color:#DFE;' as __style__, '' as author, t.id as ticket, sum(newvalue) as newvalue, strftime('%s', 'now') as time,
 'Ticket Work Summary for '||
 strftime('%m/%d/%Y %H:%M:%S', $STARTDATE, 'unixepoch', 'localtime' )||' - '||
 strftime('%m/%d/%Y %H:%M:%S', $ENDDATE, 'unixepoch', 'localtime') as strtime ,
 1 as _ord
FROM ticket_change
JOIN ticket t on t.id = ticket_change.ticket
LEFT JOIN ticket_custom as billable on billable.ticket = t.id 
  and billable.name = 'billable'
WHERE field = 'hours' and
  t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
    AND ticket_change.time >= $STARTDATE
    AND ticket_change.time < $ENDDATE
GROUP By t.id
)
ORDER BY ticket, _time,  _ord

    """
    },#END Ticket work summary
        {
    "title":"Milestone Work Summary",
    "reportnumber":None,
    "version":3,
    "sql":"""
SELECT 
  milestone as __group__, 
  __style__, 
  ticket,
  summary,
  newvalue as [Hours-added],
  time as _time,
  strtime as [Last-Updated],
 _ord
FROM(
SELECT '' as __style__, t.id as ticket, SUM(newvalue) as newvalue,t.summary as summary,
 MAX(ticket_change.time) as time,
 strftime('%m/%d/%Y %H:%M:%S', MAX(ticket_change.time), 'unixepoch', 'localtime') as strtime ,
 t.milestone as milestone,
 0  as _ord
FROM ticket_change
JOIN ticket t on t.id = ticket_change.ticket
LEFT JOIN ticket_custom as billable on billable.ticket = t.id 
  and billable.name = 'billable'
WHERE field = 'hours' and
  t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
    AND ticket_change.time >= $STARTDATE
    AND ticket_change.time < $ENDDATE
GROUP BY t.milestone, t.id

UNION 

SELECT 'background-color:#DFE;' as __style__,
 '' as ticket, sum(newvalue)  as newvalue, 
'' as summary,
strftime('%s', 'now') as time,
 'Ticket Work Summary for '||
 strftime('%m/%d/%Y %H:%M:%S', $STARTDATE, 'unixepoch', 'localtime')||' - '||
 strftime('%m/%d/%Y %H:%M:%S', $ENDDATE, 'unixepoch', 'localtime')  as strtime ,
 t.milestone as milestone,
 1 as _ord
FROM ticket_change
JOIN ticket t on t.id = ticket_change.ticket
LEFT JOIN ticket_custom as billable on billable.ticket = t.id 
  and billable.name = 'billable'
WHERE field = 'hours' and
  t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
    AND ticket_change.time >= $STARTDATE
    AND ticket_change.time < $ENDDATE
GROUP By t.milestone
)
ORDER BY milestone, ticket, _time,  _ord



    """
    },#END Milestone work summary
        
    {
    "title":"Developer Work Summary",
    "reportnumber":None,
    "version":3,
    "sql":"""
SELECT author as __group__,__style__, ticket, 
newvalue as [Hours-added], time as _time, strtime as [Time-Entered],
 _ord
FROM(
SELECT '' as __style__, author, t.id as ticket, newvalue,
 ticket_change.time as time,
 strftime('%m/%d/%Y %H:%M:%S', ticket_change.time, 'unixepoch', 'localtime') as strtime ,
 0  as _ord
FROM ticket_change
JOIN ticket t on t.id = ticket_change.ticket
LEFT JOIN ticket_custom as billable on billable.ticket = t.id 
  and billable.name = 'billable'
WHERE field = 'hours' and
  t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
    AND ticket_change.time >= $STARTDATE
    AND ticket_change.time < $ENDDATE
UNION 

SELECT 'background-color:#DFE;' as __style__, author, '' as ticket, sum(newvalue) as newvalue, strftime('%s', 'now') as time,
 'Developer Work Summary for '||
 strftime('%m/%d/%Y %H:%M:%S', $STARTDATE, 'unixepoch', 'localtime')||' - '||
 strftime('%m/%d/%Y %H:%M:%S', $ENDDATE, 'unixepoch', 'localtime') as strtime ,
 1 as _ord
FROM ticket_change
JOIN ticket t on t.id = ticket_change.ticket
LEFT JOIN ticket_custom as billable on billable.ticket = t.id 
  and billable.name = 'billable'
WHERE field = 'hours' and
  t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
    AND ticket_change.time >= $STARTDATE
    AND ticket_change.time < $ENDDATE
GROUP By author
)
ORDER BY author, _time,  _ord
    
    """
    },#END Hours Per Developer
]
ticket_hours_reports = [
{
    "title": "Ticket Hours",
    "reportnumber": None,
    "version":2,
    "sql": """
SELECT __color__,  __style__,  ticket, summary_, component ,version, severity,
 milestone, status, owner, [Estimated-hours], [total-hours], billable
--,created,  modified,         -- ## Dates are formatted
-- _description_,                    -- ## Uses a full row
-- _changetime,
-- _reporter
,_ord

FROM (
SELECT p.value AS __color__,
       '' as __style__,
       t.id AS ticket, summary AS summary_,             -- ## Break line here
       component,version, severity, milestone, status, owner,
       EstimatedHours.value as [Estimated-hours],
       totalhours.value as [total-hours], 
       CASE WHEN billable.value = 1 THEN 'Y'
            else 'N'
       END as billable,
       time AS created, changetime AS modified,         -- ## Dates are formatted
       description AS _description_,                    -- ## Uses a full row
       changetime AS _changetime,
       reporter AS _reporter
       ,0 as _ord                                        
	
  FROM ticket as t
  JOIN enum as p ON p.name=t.priority AND p.type='priority'
  
LEFT JOIN ticket_custom as EstimatedHours ON EstimatedHours.name='estimatedhours'
      AND EstimatedHours.Ticket = t.Id
LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.Ticket = t.Id
LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.Ticket = t.Id

  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
  

UNION 

SELECT 1 AS __color__,
       'background-color:#DFE;' as __style__,
       '' as ticket, 'Time Summary' AS summary_,             
       '' as component,'' as version, '' as severity, '' as  milestone, '' as status, '' as owner,
       SUM(EstimatedHours.value) as [Estimated-hours],
       SUM(totalhours.value) as [total-hours],
       '' as billable,
       '' as created, '' as modified,         -- ## Dates are formatted

       '' AS _description_,
       '' AS _changetime,
       '' AS _reporter
       ,1 as _ord
  FROM ticket as t
  JOIN enum as p ON p.name=t.priority AND p.type='priority'
  
LEFT JOIN ticket_custom as EstimatedHours ON EstimatedHours.name='estimatedhours'
      AND EstimatedHours.Ticket = t.Id

LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.Ticket = t.Id

LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.Ticket = t.Id
  
  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
)
ORDER BY ticket, _ord    
    """
    },
#END Ticket Hours 
{
    "title": "Ticket Hours with Description",
    "reportnumber": None,
    "version":2,
    "sql": """
SELECT __color__,  __style__,  ticket, summary_, component ,version, severity,
 milestone, status, owner, [Estimated-hours], [total-hours], billable
--,created,  modified,         -- ## Dates are formatted
,_description_
-- _changetime,
-- _reporter
,_ord

FROM (
SELECT p.value AS __color__,
       '' as __style__,
       t.id AS ticket, summary AS summary_,             -- ## Break line here
       component,version, severity, milestone, status, owner,
       EstimatedHours.value as [Estimated-hours],
       totalhours.value as [total-hours], 
       CASE WHEN billable.value = 1 THEN 'Y'
            else 'N'
       END as billable,
       time AS created, changetime AS modified,         -- ## Dates are formatted
       description AS _description_,                    -- ## Uses a full row
       changetime AS _changetime,
       reporter AS _reporter
       ,0 as _ord                                        
	
  FROM ticket as t
  JOIN enum as p ON p.name=t.priority AND p.type='priority'
  
LEFT JOIN ticket_custom as EstimatedHours ON EstimatedHours.name='estimatedhours'
      AND EstimatedHours.Ticket = t.Id
LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.Ticket = t.Id
LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.Ticket = t.Id

  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
  

UNION 

SELECT 1 AS __color__,
       'background-color:#DFE;' as __style__,
       '' as ticket, 'Time Summary' AS summary_,             
       '' as component,'' as version, '' as severity, '' as  milestone, '' as status, '' as owner,
       SUM(EstimatedHours.value) as [Estimated-hours],
       SUM(totalhours.value) as [total-hours],
       '' as billable,
       '' as created, '' as modified,         -- ## Dates are formatted

       '' AS _description_,
       '' AS _changetime,
       '' AS _reporter
       ,1 as _ord
  FROM ticket as t
  JOIN enum as p ON p.name=t.priority AND p.type='priority'
  
LEFT JOIN ticket_custom as EstimatedHours ON EstimatedHours.name='estimatedhours'
      AND EstimatedHours.Ticket = t.Id

LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.Ticket = t.Id

LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.Ticket = t.Id
  
  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
)
ORDER BY ticket, _ord    
    """
    },
#END Ticket Hours 

    {
    "title":"Ticket Hours Grouped By Component",
    "reportnumber":None,
    "version":2,
    "sql": """
SELECT __color__, __group__, __style__,  ticket, summary_, component ,version, severity,
 milestone, status, owner, [Estimated-hours], [total-hours], billable
--,created,  modified,         -- ## Dates are formatted
-- _description_,                    -- ## Uses a full row
-- _changetime,
-- _reporter
,_ord

FROM (
SELECT p.value AS __color__,
       t.component AS __group__,
       '' as __style__,
       t.id AS ticket, summary AS summary_,             -- ## Break line here
       component,version, severity, milestone, status, owner,
       EstimatedHours.value as [Estimated-hours],
       totalhours.value as [total-hours], 
       CASE WHEN billable.value = 1 THEN 'Y'
            else 'N'
       END as billable,
       time AS created, changetime AS modified,         -- ## Dates are formatted
       description AS _description_,                    -- ## Uses a full row
       changetime AS _changetime,
       reporter AS _reporter
       ,0 as _ord                                        
	
  FROM ticket as t
  JOIN enum as p ON p.name=t.priority AND p.type='priority'
  
LEFT JOIN ticket_custom as EstimatedHours ON EstimatedHours.name='estimatedhours'
      AND EstimatedHours.Ticket = t.Id
LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.Ticket = t.Id
LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.Ticket = t.Id

  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
  

UNION 

SELECT 1 AS __color__,
       t.component AS __group__,
       'background-color:#DFE;' as __style__,
       '' as ticket, 'Time Summary' AS summary_,             
       t.component as component,'' as version, '' as severity, '' as  milestone, '' as status, '' as owner,
       SUM(EstimatedHours.value) as [Estimated-hours],
       SUM(totalhours.value) as [total-hours],
       '' as billable,
       '' as created, '' as modified,         -- ## Dates are formatted

       '' AS _description_,
       '' AS _changetime,
       '' AS _reporter
       ,1 as _ord
  FROM ticket as t
  JOIN enum as p ON p.name=t.priority AND p.type='priority'
  
LEFT JOIN ticket_custom as EstimatedHours ON EstimatedHours.name='estimatedhours'
      AND EstimatedHours.Ticket = t.Id

LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.Ticket = t.Id

LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.Ticket = t.Id
  
  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
  GROUP BY t.component
)
ORDER BY component,ticket, _ord    
    """
    },
# END Ticket Hours  GROUPED BY COMPONENT
    
    {
    "title":"Ticket Hours Grouped By Component with Description",
    "reportnumber":None,
    "version":2,
    "sql": """
SELECT __color__, __group__, __style__,  ticket, summary_, component ,version, severity,
 milestone, status, owner, [Estimated-hours], [total-hours], billable
--,created,  modified         -- ## Dates are formatted
,_description_                    -- ## Uses a full row
-- _changetime,
-- _reporter
,_ord

FROM (
SELECT p.value AS __color__,
       t.component AS __group__,
       '' as __style__,
       t.id AS ticket, summary AS summary_,             -- ## Break line here
       component,version, severity, milestone, status, owner,
       EstimatedHours.value as [Estimated-hours],
       totalhours.value as [total-hours], 
       CASE WHEN billable.value = 1 THEN 'Y'
            else 'N'
       END as billable,
       time AS created, changetime AS modified,         -- ## Dates are formatted
       description AS _description_,                    -- ## Uses a full row
       changetime AS _changetime,
       reporter AS _reporter
       ,0 as _ord                                        
	
  FROM ticket as t
  JOIN enum as p ON p.name=t.priority AND p.type='priority'
  
LEFT JOIN ticket_custom as EstimatedHours ON EstimatedHours.name='estimatedhours'
      AND EstimatedHours.Ticket = t.Id
LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.Ticket = t.Id
LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.Ticket = t.Id

  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
  

UNION 

SELECT 1 AS __color__,
       t.component AS __group__,
       'background-color:#DFE;' as __style__,
       '' as ticket, 'Time Summary' AS summary_,             
       t.component as component,'' as version, '' as severity, '' as  milestone, '' as status, '' as owner,
       SUM(EstimatedHours.value) as [Estimated-hours],
       SUM(totalhours.value) as [total-hours],
       '' as billable,
       '' as created, '' as modified,         -- ## Dates are formatted

       '' AS _description_,
       '' AS _changetime,
       '' AS _reporter
       ,1 as _ord
  FROM ticket as t
  JOIN enum as p ON p.name=t.priority AND p.type='priority'
  
LEFT JOIN ticket_custom as EstimatedHours ON EstimatedHours.name='estimatedhours'
      AND EstimatedHours.Ticket = t.Id

LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.Ticket = t.Id

LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.Ticket = t.Id
  
  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
  GROUP BY t.component
)
ORDER BY component,ticket, _ord    
    """
    },
# END Ticket Hours Grouped BY Component with Description
    {
    "title":"Ticket Hours Grouped By Milestone",
    "reportnumber":None,
    "version":2,
    "sql": """
SELECT __color__, __group__, __style__,  ticket, summary_, component ,version, severity,
 milestone, status, owner, [Estimated-hours], [total-hours], billable
--,created,  modified,         -- ## Dates are formatted
--,_description_                    -- ## Uses a full row
-- _changetime,
-- _reporter
,_ord

FROM (
SELECT p.value AS __color__,
       t.milestone AS __group__,
       '' as __style__,
       t.id AS ticket, summary AS summary_,             -- ## Break line here
       component,version, severity, milestone, status, owner,
       EstimatedHours.value as [Estimated-hours],
       totalhours.value as [total-hours], 
       CASE WHEN billable.value = 1 THEN 'Y'
            else 'N'
       END as billable,
       time AS created, changetime AS modified,         -- ## Dates are formatted
       description AS _description_,                    -- ## Uses a full row
       changetime AS _changetime,
       reporter AS _reporter
       ,0 as _ord                                        
	
  FROM ticket as t
  JOIN enum as p ON p.name=t.priority AND p.type='priority'
  
LEFT JOIN ticket_custom as EstimatedHours ON EstimatedHours.name='estimatedhours'
      AND EstimatedHours.Ticket = t.Id
LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.Ticket = t.Id
LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.Ticket = t.Id

  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
  

UNION 

SELECT 1 AS __color__,
       t.milestone AS __group__,
       'background-color:#DFE;' as __style__,
       '' as ticket, 'Time Summary' AS summary_,             
       '' as component,'' as version, '' as severity, t.milestone as  milestone, '' as status, '' as owner,
       SUM(EstimatedHours.value) as [Estimated-hours],
       SUM(totalhours.value) as [total-hours],
       '' as billable,
       '' as created, '' as modified,         -- ## Dates are formatted

       '' AS _description_,
       '' AS _changetime,
       '' AS _reporter
       ,1 as _ord
  FROM ticket as t
  JOIN enum as p ON p.name=t.priority AND p.type='priority'
  
LEFT JOIN ticket_custom as EstimatedHours ON EstimatedHours.name='estimatedhours'
      AND EstimatedHours.Ticket = t.Id

LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.Ticket = t.Id

LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.Ticket = t.Id
  
  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
  GROUP BY t.milestone
)
ORDER BY milestone,ticket, _ord    
    """
    },
#END Ticket Hours Grouped By MileStone
        {
    "title":"Ticket Hours Grouped By MileStone with Description",
    "reportnumber":None,
    "version":2,
    "sql": """
SELECT __color__, __group__, __style__,  ticket, summary_, component ,version, severity,
 milestone, status, owner, [Estimated-hours], [total-hours], billable
--,created,  modified,         -- ## Dates are formatted
,_description_                    -- ## Uses a full row
-- _changetime,
-- _reporter
,_ord

FROM (
SELECT p.value AS __color__,
       t.milestone AS __group__,
       '' as __style__,
       t.id AS ticket, summary AS summary_,             -- ## Break line here
       component,version, severity, milestone, status, owner,
       EstimatedHours.value as [Estimated-hours],
       totalhours.value as [total-hours], 
       CASE WHEN billable.value = 1 THEN 'Y'
            else 'N'
       END as billable,
       time AS created, changetime AS modified,         -- ## Dates are formatted
       description AS _description_,                    -- ## Uses a full row
       changetime AS _changetime,
       reporter AS _reporter
       ,0 as _ord                                        
	
  FROM ticket as t
  JOIN enum as p ON p.name=t.priority AND p.type='priority'
  
LEFT JOIN ticket_custom as EstimatedHours ON EstimatedHours.name='estimatedhours'
      AND EstimatedHours.Ticket = t.Id
LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.Ticket = t.Id
LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.Ticket = t.Id

  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
  

UNION 

SELECT 1 AS __color__,
       t.milestone AS __group__,
       'background-color:#DFE;' as __style__,
       '' as ticket, 'Time Summary' AS summary_,             
       '' as component,'' as version, '' as severity, t.milestone as  milestone, '' as status, '' as owner,
       SUM(EstimatedHours.value) as [Estimated-hours],
       SUM(totalhours.value) as [total-hours],
       '' as billable,
       '' as created, '' as modified,         -- ## Dates are formatted

       '' AS _description_,
       '' AS _changetime,
       '' AS _reporter
       ,1 as _ord
  FROM ticket as t
  JOIN enum as p ON p.name=t.priority AND p.type='priority'
  
LEFT JOIN ticket_custom as EstimatedHours ON EstimatedHours.name='estimatedhours'
      AND EstimatedHours.Ticket = t.Id

LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.Ticket = t.Id

LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.Ticket = t.Id
  
  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
  GROUP BY t.milestone
)
ORDER BY milestone,ticket, _ord    
    """
    }
    #END Ticket Hours Grouped By MileStone with Description
]
    
all_reports = [
    {"title":"Billing Reports",
     "reports":billing_reports},
    {"title":"Ticket/Hour Reports",
     "reports": ticket_hours_reports}
    ]
