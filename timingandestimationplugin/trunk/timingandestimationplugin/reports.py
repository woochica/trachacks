# IF YOU ADD A NEW SECTION OF REPORTS, You will need to make
# sure that section is also added to the all_reports hashtable
# near the bottom

#Please try to keep this clean"

billing_reports = [
        {
    "title":"Ticket Work Summary",
    "reportnumber":None,
    "version":7,
    "sql":"""
SELECT ticket as __group__, __style__, ticket,
newvalue as Hours_added, author, time,

-- strtime as Time_Entered,

 _ord
FROM(
SELECT '' as __style__, author, t.id as ticket, newvalue,
 ticket_change.time as time,
 
-- strftime('%m/%d/%Y %H:%M:%S', ticket_change.time, 'unixepoch', 'localtime') as strtime ,

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

SELECT 'background-color:#DFE;' as __style__, 'Ticket Work Summary for the selected time period ' as author, t.id as ticket, sum(newvalue) as newvalue, NULL as time,

-- 'Ticket Work Summary for the selected time period '
-- ||
-- strftime('%m/%d/%Y %H:%M:%S', STARTDATE, 'unixepoch', 'localtime' )||' - '||
-- strftime('%m/%d/%Y %H:%M:%S', ENDDATE, 'unixepoch', 'localtime') as strtime ,

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
)  as tbl
ORDER BY ticket,  _ord , time

    """
    },#END Ticket work summary
        {
    "title":"Milestone Work Summary",
    "reportnumber":None,
    "version":7,
    "sql":"""

SELECT 
  milestone as __group__, 
  __style__, 
  ticket,
  summary,
  newvalue as Hours_added,
  time as Last_Updated,
--  strtime as Last_Updated,
 _ord
FROM(
SELECT '' as __style__, t.id as ticket, SUM(newvalue) as newvalue,t.summary as summary,
 MAX(ticket_change.time) as time,

-- strftime('%m/%d/%Y %H:%M:%S', MAX(ticket_change.time), 'unixepoch', 'localtime') as strtime ,

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
 NULL as ticket, sum(newvalue)  as newvalue, 
'' as summary,
NULL as time,

-- 'Ticket Work Summary for '||
-- strftime('%m/%d/%Y %H:%M:%S', STARTDATE, 'unixepoch', 'localtime')||' - '||
-- strftime('%m/%d/%Y %H:%M:%S', ENDDATE, 'unixepoch', 'localtime')  as strtime ,

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
)  as tbl
ORDER BY milestone, ticket, time,  _ord



    """
    },#END Milestone work summary
        
    {
    "title":"Developer Work Summary",
    "reportnumber":None,
    "version":6,
    "sql":"""
SELECT author as __group__,__style__, ticket, 
newvalue as Hours_added, time as time,

-- strtime as Time_Entered,

 _ord
FROM(
SELECT '' as __style__, author, t.id as ticket, newvalue,
 ticket_change.time as time,

-- strftime('%m/%d/%Y %H:%M:%S', ticket_change.time, 'unixepoch', 'localtime') as strtime ,

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

SELECT 'background-color:#DFE;' as __style__, author,
NULL as ticket, sum(newvalue) as newvalue, NULL as time,

-- 'Developer Work Summary for '||
-- strftime('%m/%d/%Y %H:%M:%S', STARTDATE, 'unixepoch', 'localtime')||' - '||
-- strftime('%m/%d/%Y %H:%M:%S', ENDDATE, 'unixepoch', 'localtime') as strtime ,

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
)  as tbl
ORDER BY author, time,  _ord
    
    """
    },#END Hours Per Developer
]
ticket_hours_reports = [
{
    "title": "Ticket Hours",
    "reportnumber": None,
    "version":4,
    "sql": """
SELECT __color__,  __style__,  ticket, summary_, component ,version, severity,
 milestone, status, owner, Estimated_hours, total_hours, billable
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
       EstimatedHours.value as Estimated_hours,
       totalhours.value as total_hours, 
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
       NULL as ticket, 'Time Summary' AS summary_,             
       NULL as component,NULL as version, NULL as severity, NULL as  milestone, NULL as status, NULL as owner,
       SUM(EstimatedHours.value) as Estimated_hours,
       SUM(totalhours.value) as total_hours,
       NULL as billable,
       NULL as created, NULL as modified,         -- ## Dates are formatted

       NULL AS _description_,
       NULL AS _changetime,
       NULL AS _reporter
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
)  as tbl
ORDER BY ticket, _ord    
    """
    },
#END Ticket Hours 
{
    "title": "Ticket Hours with Description",
    "reportnumber": None,
    "version":4,
    "sql": """
SELECT __color__,  __style__,  ticket, summary_, component ,version, severity,
 milestone, status, owner, Estimated_hours, total_hours, billable
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
       EstimatedHours.value as Estimated_hours,
       totalhours.value as total_hours, 
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
       NULL as ticket, 'Time Summary' AS summary_,             
       NULL as component,NULL as version, NULL as severity, NULL as  milestone, NULL as status, NULL as owner,
       SUM(EstimatedHours.value) as Estimated_hours,
       SUM(totalhours.value) as total_hours,
       NULL as billable,
       NULL as created, NULL as modified,         -- ## Dates are formatted

       NULL AS _description_,
       NULL AS _changetime,
       NULL AS _reporter
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
)  as tbl
ORDER BY ticket, _ord    
    """
    },
#END Ticket Hours 

    {
    "title":"Ticket Hours Grouped By Component",
    "reportnumber":None,
    "version":4,
    "sql": """
SELECT __color__, __group__, __style__,  ticket, summary_, component ,version, severity,
 milestone, status, owner, Estimated_hours, total_hours, billable
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
       EstimatedHours.value as Estimated_hours,
       totalhours.value as total_hours, 
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
       NULL as ticket, 'Time Summary' AS summary_,             
       t.component as component,NULL as version, NULL as severity, NULL as  milestone, NULL as status,
       NULL as owner,
       SUM(EstimatedHours.value) as Estimated_hours,
       SUM(totalhours.value) as total_hours,
       NULL as billable,
       NULL as created,
       NULL as modified,         -- ## Dates are formatted

       NULL AS _description_,
       NULL AS _changetime,
       NULL AS _reporter
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
)  as tbl
ORDER BY component,ticket, _ord    
    """
    },
# END Ticket Hours  GROUPED BY COMPONENT
    
    {
    "title":"Ticket Hours Grouped By Component with Description",
    "reportnumber":None,
    "version":4,
    "sql": """
SELECT __color__, __group__, __style__,  ticket, summary_, component ,version, severity,
 milestone, status, owner, Estimated_hours, total_hours, billable
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
       EstimatedHours.value as Estimated_hours,
       totalhours.value as total_hours, 
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
       NULL as ticket, 'Time Summary' AS summary_,             
       t.component as component,NULL as version, NULL as severity, NULL as  milestone, NULL as status, NULL as owner,
       SUM(EstimatedHours.value) as Estimated_hours,
       SUM(totalhours.value) as total_hours,
       NULL as billable,
       NULL as created, NULL as modified,         -- ## Dates are formatted

       NULL AS _description_,
       NULL AS _changetime,
       NULL AS _reporter
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
)  as tbl
ORDER BY component,ticket, _ord    
    """
    },
# END Ticket Hours Grouped BY Component with Description
    {
    "title":"Ticket Hours Grouped By Milestone",
    "reportnumber":None,
    "version":4,
    "sql": """
SELECT __color__, __group__, __style__,  ticket, summary_, component ,version, severity,
 milestone, status, owner, Estimated_hours, total_hours, billable
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
       EstimatedHours.value as Estimated_hours,
       totalhours.value as total_hours, 
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
       NULL as ticket, 'Time Summary' AS summary_,             
       NULL as component,NULL as version, NULL as severity, t.milestone as  milestone,
       NULL as status, NULL as owner,
       SUM(EstimatedHours.value) as Estimated_hours,
       SUM(totalhours.value) as total_hours,
       NULL as billable,
       NULL as created, NULL as modified,         -- ## Dates are formatted

       NULL AS _description_,
       NULL AS _changetime,
       NULL AS _reporter
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
)  as tbl
ORDER BY milestone,ticket, _ord    
    """
    },
#END Ticket Hours Grouped By MileStone
        {
    "title":"Ticket Hours Grouped By MileStone with Description",
    "reportnumber":None,
    "version":4,
    "sql": """
SELECT __color__, __group__, __style__,  ticket, summary_, component ,version, severity,
 milestone, status, owner, Estimated_hours, total_hours, billable
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
       EstimatedHours.value as Estimated_hours,
       totalhours.value as total_hours, 
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
       NULL as ticket, 'Time Summary' AS summary_,             
       NULL as component,NULL as version, NULL as severity, t.milestone as  milestone,
       NULL as status, NULL as owner,
       SUM(EstimatedHours.value) as Estimated_hours,
       SUM(totalhours.value) as total_hours,
       NULL as billable,
       NULL as created, NULL as modified,         -- ## Dates are formatted

       NULL AS _description_,
       NULL AS _changetime,
       NULL AS _reporter
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
)  as tbl
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
