#include "trac2xml.h"
#include "projectxml.h"
#include <QDebug>
#include <QTextOStream>
#include <QFileDialog>
#include <QFile>


CTrac2xml::CTrac2xml(QWidget *parent, Qt::WFlags flags)
	: QWidget(parent, flags),
	m_connection(this)
{
	QCoreApplication::setOrganizationName("Netstream ");
	QCoreApplication::setOrganizationDomain("netstream.ru");
	QCoreApplication::setApplicationName("trac2project");
	
	m_ui.setupUi(this);
	m_ui.m_progressBar->setVisible(false);

	Q_ASSERT( 
		connect( &m_connection, SIGNAL(ticketCountRecieved( int )),
		this, SLOT(onTicketCountRecieved( int ) ) ) 
		);

	Q_ASSERT( 
		connect( &m_connection, SIGNAL(ticketInfoRecieved( QVariant )),
		this, SLOT(incProgress( ) ) ) 
		);

	Q_ASSERT( 
		connect( &m_connection, SIGNAL(ticketUpdated( )),
		this, SLOT(incProgress(  ) ) ) 
		);

	Q_ASSERT( 
		connect( &m_connection, SIGNAL(ticketsRecieved(QVariantList)),
		this, SLOT(onTicketsRecieved( QVariantList ) ) ) 
		);

	Q_ASSERT( 
		connect( &m_connection, SIGNAL(ticketsUpdated(QList<QMap<QString,QVariant> > )),
		this, SLOT(onTicketsUpdated( QList<QMap<QString,QVariant> >  ) ) ) 
		);

	loadConnectionInfo();
}

CTrac2xml::~CTrac2xml()
{

}

void CTrac2xml::on_m_createXml_clicked()
{
	setConnectInfo();
	m_tickets.clear();
	requestTickets(m_ui.m_query->text());
}

void CTrac2xml::on_m_toTrac_clicked()
{
	setConnectInfo();
	CProjectXml proj;
	bool res=proj.loadTicketsFromXml(QFileDialog::getOpenFileName(this,
		tr("Open Project Xml"), "", tr("Project Xml Files (*.xml)")));
	if (res)
	{
		m_connection.requestForTicketsUpdate(proj.getTickets());
		m_ui.m_progressBar->setMinimum(0);
		m_ui.m_progressBar->setMaximum(proj.getTickets().count());
		m_ui.m_progressBar->setVisible(true);
		setEnabled(false);
	}
}

void CTrac2xml::onTicketCountRecieved( int a_count )
{
	m_ui.m_progressBar->setMaximum(a_count);
	m_ui.m_progressBar->setValue(0);
}

void CTrac2xml::incProgress( )
{
	m_ui.m_progressBar->setValue(m_ui.m_progressBar->value()+1);
}

void CTrac2xml::onTicketsRecieved( QVariantList a_tickets )
{
	CProjectXml proj;
	m_tickets.append(a_tickets);
	if ( proj.loadTicketsFromVariantList(m_tickets) )
	{
		QString name=QFileDialog::getSaveFileName();
		if (!name.isEmpty())
		{
			QFile  f(name);
			f.open(QIODevice::WriteOnly|QIODevice::Truncate);
			QString a=proj.getXmlFromTickets();
			f.write(a.toUtf8());
			f.close();
		}
	}
	else
	{
		if (proj.getLostTickets().count()>0) // Перезапросим у сервера все тикеты , включая потерянные
		{
			QListIterator<int> i(proj.getLostTickets());
			QString temp="id=%1";
			QString query;
			while(i.hasNext())
				query +="&" + temp.arg(i.next()  );
		
			requestTickets(query.remove(0,1));
		}
	}
	setEnabled(true);
	
}

void CTrac2xml::onTicketsUpdated( QList<QMap<QString,QVariant> >  a_errorTickets )
{

	setEnabled(true);
}

void CTrac2xml::setConnectInfo()
{
	m_connection.setUrl(m_ui.m_url->text(),m_ui.m_port->value());
	m_connection.setUser(m_ui.m_login->text(),m_ui.m_password->text() );
	QSettings settings;
	settings.setValue("url",m_ui.m_url->text());
	settings.setValue("port",m_ui.m_port->value());
	settings.setValue("login",m_ui.m_login->text());
	settings.setValue("password",m_ui.m_password->text() );
	settings.setValue("query",m_ui.m_query->text());

	

}

void CTrac2xml::loadConnectionInfo()
{
	QSettings settings;

	QString url=settings.value("url").toString();
	if (!url.isEmpty())
		m_ui.m_url->setText(url);

	int port=settings.value("port").toInt();
	if (port!=0)
		m_ui.m_port->setValue(port);
	m_ui.m_login->setText(settings.value("login").toString());

	m_ui.m_password->setText(settings.value("password").toString() );

	QString query=settings.value("query").toString();
	if (!query.isEmpty())
		m_ui.m_query->setText(query);
}

void CTrac2xml::requestTickets( const QString & a_query )
{
	m_connection.requestTickets(a_query);
	m_ui.m_progressBar->setVisible(true);
	setEnabled(false);
}