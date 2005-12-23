import xmlrpclib

server = xmlrpclib.ServerProxy("http://athomas:password@localhost/trac-dev/login/RPC2")

#print '\n'.join(map(str, server.tracrpc.ticket.query_tickets("owner=athomas")))

#print server.tracrpc.ticket.create_ticket(
#    'Moo', 'Mooo barreed', {
#        'component' : 'component1',
#    })

print '\n'.join(map(str, server.tracrpc.ticket.get_components()))
