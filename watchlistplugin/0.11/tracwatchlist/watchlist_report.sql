-- Watched tickets --

-- This report lists all tickets in the users [/watchlist#tickets watchlist].

SELECT p.value AS __color__,
   (CASE status WHEN 'accepted' THEN 'Accepted' ELSE 'Owned' END) AS __group__,
   id AS ticket, summary, component, version, milestone,
   t.type AS type, priority, time AS created,
   changetime AS _changetime, description AS _description,
   reporter AS _reporter
  FROM ticket t
  LEFT JOIN enum p ON p.name = t.priority AND p.type = 'priority'
  WHERE id IN (SELECT resid FROM watchlist WHERE wluser = '$USER' AND realm = 'ticket')
  ORDER BY (status = 'accepted') DESC, CAST(p.value AS int), milestone, t.type, time

