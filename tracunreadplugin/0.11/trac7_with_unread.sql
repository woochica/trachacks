-- My Tickets (with read / unread marks)
-- This is basically same as report:7, but with "unread" column
-- Of course, you must be logged in to use it (just like report:7).

SELECT p.value AS __color__,
   (CASE status WHEN 'assigned' THEN 'Assigned' ELSE 'Owned' END) AS __group__,
   t.id AS ticket, summary, component,
   priority, time AS _created,
   changetime AS modified,
   reporter AS _reporter
   , CASE
    WHEN u.last_read_on IS NULL OR u.last_read_on < t.time
    THEN '[ticket:' || cast(t.id AS char) || ' new ticket]'
    WHEN u.last_read_on > t.changetime
    THEN 'no unread'
    ELSE '[comment:ticket:' || cast(t.id AS char) || ':' || (
        -- fetch unread comment number
        SELECT
          CASE
            -- Thanks for recording parent.child relationship, guys!
            WHEN position('.' in oldvalue) != 0 THEN split_part(oldvalue, '.', 2)
            ELSE oldvalue
          END
        FROM ticket_change tc
        WHERE field = 'comment'
          AND ticket = t.id
          AND time > u.last_read_on
        ORDER BY time
        LIMIT 1
      ) || ' unread comment]'
    END
    AS description

  FROM ticket t
  LEFT JOIN enum p ON p.name = t.priority AND p.type = 'priority'
  LEFT JOIN trac_unread u ON (u.id=t.id
    AND u.type = 'ticket'
    AND u.username = '$USER'
  )
  WHERE t.status IN ('new', 'assigned', 'reopened') AND owner = '$USER'
  ORDER BY (status = 'assigned') DESC, CAST(p.value AS integer), milestone, t.type, time

