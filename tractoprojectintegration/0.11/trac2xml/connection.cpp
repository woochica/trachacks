#include "connection.h"
#include "projectxml.h"

CConnection::CConnection(QObject *parent)
	: QObject(parent),
		m_ticketListRequest(-1),
		m_ticketUpdateRequest(-1)
{
	m_xmlrpc = new xmlrpc::Client(this);

	Q_ASSERT( 
		connect( m_xmlrpc, SIGNAL(done( int, QVariant )),
		this, SLOT(processReturnValue( int, QVariant )) ) 
		);
	Q_ASSERT( 
		connect( m_xmlrpc, SIGNAL(failed( int, int, QString )),
		this, SLOT(processFault( int, int, QString )) ) 
		);
}

CConnection::~CConnection()
{

}



void CConnection::setUrl(const QString &  a_url,int a_port)
{
	QUrl u(a_url);
	m_xmlrpc->setHost(u.host(),a_port,u.path());
}



void CConnection::setUser( const QString & a_login,const QString & a_password )
{
		m_xmlrpc->setUser(a_login,a_password);
}

void CConnection::requestTickets(const QString a_requset)
{
	m_ticketListRequest=m_xmlrpc->request("ticket.query",a_requset);
}


void CConnection::requestTicketInfo( int a_id )
{
	m_ticketInfoRequest=m_xmlrpc->request("ticket.get",a_id);
}




int CConnection::requestForTicketUpdate(QMap<QString,QVariant> a_ticket )
{
	QMap<QString,xmlrpc::Variant> t;//=a_ticket;
	int id=a_ticket[ticket_id].toInt();
	//  К сожалению, из-за обоснованных ограничейний  xmlrpc::Variant красиво преобразовать a_ticket не получится
	t.insert(ticket_summary,a_ticket[ticket_summary].toString()  );
	t.insert(ticket_duration,a_ticket[ticket_duration].toString()  );
	t.insert(ticket_owner,a_ticket[ticket_owner].toString() );
	t.insert(ticket_due_assign,a_ticket[ticket_due_assign].toString() );
	//t.insert(ticket_due_assign,xmlrpc::Variant(a_ticket[ticket_due_assign] ) );
	return m_xmlrpc->request("ticket.update",id,trUtf8(""),t,true);
}




void CConnection::requestForTicketsUpdate( QList<QMap<QString,QVariant> > a_tickets )
{
	if (m_ticketsForUpdate.count()>0)
	{
		qDebug() << "Go to the dick from the beach. Update process is already started." ; 
		return;
	}
	m_ticketsForUpdate=a_tickets;
	m_errorTickets.clear();
	if (m_ticketsForUpdate.count()>0)
		m_ticketUpdateRequest=requestForTicketUpdate(m_ticketsForUpdate[0]);
	else
		emit ticketsUpdated(m_errorTickets);
}


void CConnection::startRequestInfoForAllTickets( QVariant a_ids )
{
	if ( a_ids.canConvert(QVariant::List) ) 
	{
		m_idsForRequest.clear();
		m_tickets.clear();
		QListIterator<QVariant> l=a_ids.toList();
		while(l.hasNext())
		{
			QVariant current=l.next();
			if (current.canConvert(QVariant::Int))
				m_idsForRequest.append(current.toInt());
			else
			{
				qDebug() << "Ticket id " << current << " is not integer";
				break;
			}
		}
	}
	if (!m_idsForRequest.isEmpty())
		requestTicketInfo(m_idsForRequest[0]);
}



void CConnection::onTicketUpdated()
{
	
	m_ticketsForUpdate.removeAt(0);
	if (m_ticketsForUpdate.isEmpty())
		emit ticketsUpdated(m_errorTickets);
	else
		m_ticketUpdateRequest=requestForTicketUpdate(m_ticketsForUpdate[0]);
	emit ticketUpdated();
}

void CConnection::onTicketInfoRecieved( QVariant a_value )
{
	m_tickets.append(a_value);
	m_idsForRequest.removeAt(0);
	if (m_idsForRequest.isEmpty())
		emit ticketsRecieved(m_tickets);
	else
		requestTicketInfo(m_idsForRequest[0]);
	emit ticketInfoRecieved(a_value);
}


void CConnection::processReturnValue( int a_requestId, QVariant a_value )
{
	if (a_requestId==m_ticketListRequest)
	{
		startRequestInfoForAllTickets(a_value);
		if ( a_value.canConvert(QVariant::List) )
			emit ticketCountRecieved(a_value.toList().count());
		else
			qDebug() << "Parse error: " << a_value << " is not a list";
	}
	if (a_requestId==m_ticketInfoRequest)
		onTicketInfoRecieved(a_value);
	if(a_requestId==m_ticketUpdateRequest)
		onTicketUpdated();


}

void CConnection::processFault( int a_requestId, int a_errorCode, QString a_errorString )
{
	if (a_requestId==m_ticketUpdateRequest)
	{
		qDebug() << "Error during update ticket.  Error code= " << a_errorCode << " "  << a_errorString;
		emit ticketUpdated();
		m_errorTickets.append(m_ticketsForUpdate[0]);
		onTicketUpdated();
	}
}