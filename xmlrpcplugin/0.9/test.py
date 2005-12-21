import xmlrpclib

server = xmlrpclib.ServerProxy("http://athomas:password@localhost/trac-dev/RPC2")

#print server.tracrpc.api.list_xmlrpc_functions()
#
print server.tracrpc.ticket.query_tickets("owner=athomas")

#print server.tracrpc.ticket.create_ticket(
#    'new', 'Moo', 'Mooo barreed', 'athomas', '', 'defect',
#    'component1', 'major', 'athomas',
#    '1.0', 'milestone1', ''
#    )
