import xmlrpclib

server = xmlrpclib.ServerProxy("http://athomas:password@localhost/trac-dev/login/RPC2")

#print '\n'.join(map(str, server.tracrpc.ticket.query_tickets("owner=athomas")))

#print server.tracrpc.ticket.create_ticket(
#    'Moo', 'Mooo barreed', {
#        'component' : 'component1',
#    })

#t = server.tracrpc.ticket.fetch_ticket(1)

print server.tracrpc.ticket.update_ticket(1, '', {
    'component' : 'component2'
    })

print server.tracrpc.ticket.get_changelog(1)

#print '\n'.join(map(str, server.tracrpc.milestone.get_milestones()))
