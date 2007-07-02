from trac.ticket.model import AbstractEnum
from webadmin.ticket import AbstractEnumAdminPage


class Client(AbstractEnum):
    type = 'client'
    custom = True  


class ClientAdminPage(AbstractEnumAdminPage):
    _type = 'client'
    _enum_cls = Client
    _label = ('Client', 'Clients')
