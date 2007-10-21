# IF YOU ADD A NEW SECTION OF REPORTS, You will need to make
# sure that section is also added to the reports hashtable
# near the bottom

# Please try to keep this clean

billing_reports = [{
    'uuid':        'cd175fb0-0c74-48e4-816f-d72b4ba98fc1',
    'title':       'Client Work Summary',
    'description': '',
    'version':     1,
    'sql':         """
SELECT 
  __group__, __style__,  ticket, summary, newvalue as Work_added,
  time, _ord
FROM(
  SELECT '' as __style__, t.id as ticket,
    SUM(CAST(newvalue as DECIMAL)) as newvalue, t.summary as summary,
    MAX(ticket_change.time) as time, client.value as __group__, 0 as _ord
  FROM ticket_change
  JOIN ticket t on t.id = ticket_change.ticket
  LEFT JOIN ticket_custom as billable on billable.ticket = t.id 
    and billable.name = 'billable'
  LEFT JOIN ticket_custom as client on client.ticket = t.id
    and client.name = 'client'
  WHERE field = 'hours' and
    t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
      AND billable.value in ($BILLABLE, $UNBILLABLE)
      AND ticket_change.time >= $STARTDATE
      AND ticket_change.time < $ENDDATE
  GROUP BY client.value, t.id, t.summary
  
  UNION 
  
  SELECT 'background-color:#DFE;' as __style__, NULL as ticket,
    sum(CAST(newvalue as DECIMAL)) as newvalue, 'Total work done' as summary,
    NULL as time, client.value as __group__, 1 as _ord
  FROM ticket_change
  JOIN ticket t on t.id = ticket_change.ticket
  LEFT JOIN ticket_custom as billable on billable.ticket = t.id 
    and billable.name = 'billable'
  LEFT JOIN ticket_custom as client on client.ticket = t.id
    and client.name = 'client'
  WHERE field = 'hours' and
    t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
      AND billable.value in ($BILLABLE, $UNBILLABLE)
      AND ticket_change.time >= $STARTDATE
      AND ticket_change.time < $ENDDATE
  GROUP By client.value
)  as tbl
ORDER BY __group__,  _ord ASC, ticket, time
    """
    }]

ticket_hours_reports = [{
    'uuid':        'e2ab8124-9309-4d1c-9cec-f8c7b11bf579',
    'title':       'Ticket Hours Grouped By Client',
    'description': '',
    'version':     1,
    'sql':         """
SELECT __color__, __group__, __style__, ticket, summary, __component__ ,version,
  severity, milestone, status, owner, estimate_work, total_work, billable,
  _ord

FROM (
SELECT p.value AS __color__,
       client.value AS __group__,
       '' as __style__,
       t.id AS ticket, summary AS summary,             -- ## Break line here
       component as __component__,version, severity, milestone, status, owner,
       CAST(estimatedhours.value as DECIMAL) as estimate_work,
       CAST(totalhours.value as DECIMAL) as Total_work,
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
  
LEFT JOIN ticket_custom as estimatedhours ON estimatedhours.name='estimatedhours'
      AND estimatedhours.ticket = t.id
LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.ticket = t.id
LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.ticket = t.id
LEFT JOIN ticket_custom as client ON client.name='client'
      AND client.ticket = t.id

  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
  

UNION 

SELECT '1' AS __color__,
       client.value AS __group__,
       'background-color:#DFE;' as __style__,
       NULL as ticket, 'Total work' AS summary,             
       t.component as __component__, NULL as version, NULL as severity,
       NULL as  milestone, NULL as status,
       NULL as owner,
       SUM(CAST(estimatedhours.value as DECIMAL)) as estimate_work,
       SUM(CAST(totalhours.value as DECIMAL)) as Total_work,
       NULL as billable,
       NULL as created,
       NULL as modified,         -- ## Dates are formatted

       NULL AS _description_,
       NULL AS _changetime,
       NULL AS _reporter
       ,1 as _ord
  FROM ticket as t
  JOIN enum as p ON p.name=t.priority AND p.type='priority'
  
LEFT JOIN ticket_custom as estimatedhours ON estimatedhours.name='estimatedhours'
      AND estimatedhours.ticket = t.id

LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.ticket = t.id

LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.ticket = t.id
  
LEFT JOIN ticket_custom as client ON client.name='client'
      AND client.ticket = t.id
  
  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
  GROUP BY client.value
)  as tbl
ORDER BY __group__, _ord ASC,ticket
    """
    },{
    'uuid':        '9194d297-bd5a-4225-a28c-e981525b20e1',
    'title':       'Ticket Hours Grouped By Client with Description',
    'description': '',
    'version':     1,
    'sql':         """
SELECT __color__, __group__, __style__, ticket, summary, __component__ ,version,
  severity, milestone, status, owner, estimate_work, total_work, billable,
  _description_, _ord

FROM (
SELECT p.value AS __color__,
       client.value AS __group__,
       '' as __style__,
       t.id AS ticket, summary AS summary,             -- ## Break line here
       component as __component__,version, severity, milestone, status, owner,
       CAST(estimatedhours.value as DECIMAL) as estimate_work,
       CAST(totalhours.value as DECIMAL) as Total_work,
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
  
LEFT JOIN ticket_custom as estimatedhours ON estimatedhours.name='estimatedhours'
      AND estimatedhours.ticket = t.id
LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.ticket = t.id
LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.ticket = t.id
LEFT JOIN ticket_custom as client ON client.name='client'
      AND client.ticket = t.id

  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
  

UNION 

SELECT '1' AS __color__,
       client.value AS __group__,
       'background-color:#DFE;' as __style__,
       NULL as ticket, 'Total work' AS summary,             
       t.component as __component__, NULL as version, NULL as severity,
       NULL as  milestone, NULL as status,
       NULL as owner,
       SUM(CAST(estimatedhours.value as DECIMAL)) as estimate_work,
       SUM(CAST(totalhours.value as DECIMAL)) as Total_work,
       NULL as billable,
       NULL as created,
       NULL as modified,         -- ## Dates are formatted

       NULL AS _description_,
       NULL AS _changetime,
       NULL AS _reporter
       ,1 as _ord
  FROM ticket as t
  JOIN enum as p ON p.name=t.priority AND p.type='priority'
  
LEFT JOIN ticket_custom as estimatedhours ON estimatedhours.name='estimatedhours'
      AND estimatedhours.ticket = t.id

LEFT JOIN ticket_custom as totalhours ON totalhours.name='totalhours'
      AND totalhours.ticket = t.id

LEFT JOIN ticket_custom as billable ON billable.name='billable'
      AND billable.ticket = t.id
  
LEFT JOIN ticket_custom as client ON client.name='client'
      AND client.ticket = t.id
  
  WHERE t.status IN ($NEW, $ASSIGNED, $REOPENED, $CLOSED) 
    AND billable.value in ($BILLABLE, $UNBILLABLE)
  GROUP BY client.value
)  as tbl
ORDER BY __group__, _ord ASC,ticket
    """
    }]


reports = [{
    'title':   'Billing Reports',
    'reports': billing_reports
    },{
    'title':   'Ticket/Hour Reports',
    'reports': ticket_hours_reports
    }]
    
