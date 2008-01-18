#!/usr/bin/python

project = 'blueocean'
title = 'BlueOcean'
reports = [
{
  'title': 'Tickets por Milestone',
  'sql': 'SELECT DISTINCT name FROM milestone',
  'queries': [
    {
      'title': '${item} tickets',
      'type': 'p3',
      'filename': 'milestone_tickets',
      'sql': 'SELECT priority, count(*) AS total FROM ticket WHERE milestone="${item}" GROUP BY priority ORDER BY priority'
    }
  ]
},
{
  'title': 'Tickets por Component',
  'sql': 'SELECT DISTINCT name FROM component',
  'queries': [
    {
      'title': '${item} tickets',
      'type': 'p3',
      'filename': 'component_tickets',
      'sql': 'SELECT priority, count(*) AS total FROM ticket WHERE component="${item}" GROUP BY priority ORDER BY priority'
    }
  ]
},
{
  'title': 'Tickets por Resolution',
  'sql': 'SELECT DISTINCT priority FROM ticket',
  'queries': [
    {
      'title': '${item} tickets',
      'type': 'p3',
      'filename': 'resolution_tickets',
      'sql': 'SELECT resolution, count(*) AS total FROM ticket WHERE priority="${item}" GROUP BY resolution ORDER BY resolution'
    }
  ]
},
{
  'title': 'Tickets por Status',
  'sql': 'SELECT DISTINCT priority FROM ticket',
  'queries': [
    {
      'title': '${item} tickets',
      'type': 'p3',
      'filename': 'status_tickets',
      'sql': 'SELECT status, count(*) AS total FROM ticket WHERE priority="${item}" GROUP BY status ORDER BY status'
    }
  ]
},
{
  'title': 'Tickets por Owner',
  'sql': 'SELECT DISTINCT owner FROM ticket',
  'queries': [
    {
      'title': '${item} query abc',
      'type': 'p3',
      'filename': 'owner_tickets',
      'sql': 'SELECT priority, count(*) AS total FROM ticket WHERE owner="${item}" GROUP BY priority ORDER BY priority'
    }
  ]
}
]

