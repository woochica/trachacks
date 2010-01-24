#include "projectxml.h"
#include <QDebug>
#include <QFile>
#include <QStringList>
#include <QDateTime>


#define xml_UID "UID"
#define xml_component "component"
#define xml_summary "Name"
#define xml_description "Notes"
#define xml_duration "Duration"
#define xml_due_assign "Start"
#define xml_constraintdate "ConstraintDate"
#define xml_actualWork "ActualWork"
#define xml_owner "owner"
#define xml_predecessorUID "PredecessorUID"
#define xml_predecessorLink "PredecessorLink"
#define xml_Resource "Resource"
#define xml_Task "Task"
#define xml_TaskUID "TaskUID"
#define xml_ResourceUID "ResourceUID"
#define xml_RemainingWork "RemainingWork"
#define xml_Assignment "Assignment"

CProjectXml::CProjectXml(QObject *parent)
	: QObject(parent)
	,m_template("Project xml")
{
	
}

CProjectXml::~CProjectXml()
{

}

bool  CProjectXml::loadTicketsFromVariantList( QVariantList a_tickets )
{
	QListIterator<QVariant> i(a_tickets);
	m_tickets.clear();
	while(i.hasNext())
	{
		QVariant val=i.next();
		QMap<QString,QVariant> ticket =ticketFromVariant(val);
		if (ticket.isEmpty())
		{
			qDebug() << "Found an bad ticket. Check the log above." << val;
			return false;
		}
		m_tickets.append(ticket);
	}
	// А теперь , когда все тикеты добавлены в хеш можно смело проверять каких не хватает 
	if ( checkForLostTickets() )
		return false;


}

QString CProjectXml::getXmlFromTickets()
{
	QFile file(":/CTrac2xml/Resources/template.xml");
	if (!file.open(QIODevice::ReadOnly))
		return QString();
	if (!m_template.setContent(&file)) {
		file.close();
		return QString();
	}
	file.close();

	QDomDocument dom(m_template);

	// Ресурсы
	m_owners=getOwners(m_tickets);
	QDomNodeList resourceList=dom.elementsByTagName(xml_Resource);
	if (!resourceList.isEmpty())
	{
		QDomElement resourceTemplate=resourceList.at(0).toElement();
		if (!resourceTemplate.isNull())
		{
			QDomElement resources=resourceTemplate.parentNode().toElement();
			if (!resources.isNull())
				for(int i=0;i<m_owners.count();i++)
					createResourceElement(m_owners[i],i+1,resources,resourceTemplate);
		}	
	}

	// Таски
	QDomNodeList taskList=dom.elementsByTagName(xml_Task);
	if (!taskList.isEmpty())
	{
		QDomNode taskNode=taskList.at(0);
		QDomElement old=taskNode.toElement();
		if (!old.isNull())
		{
			QDomElement tasksElement=old.parentNode().toElement();
			QDomElement newTask=old.cloneNode().toElement();
			// Пройдемся по тикетам
			QListIterator< QMap<QString,QVariant> > i(m_tickets);
			while (i.hasNext())
			{
				QMap<QString,QVariant> ticket= i.next();
				createTaskElement(ticket,tasksElement,old);
			}
			
			//Удалим шаблонный таск
			tasksElement.removeChild(old);
		}
	}

	// Связь тасков с ресурсами
	QDomNodeList assignmentList=dom.elementsByTagName(xml_Assignment);
	if (!assignmentList.isEmpty())
	{
		
		QDomElement assignmentTemplate=assignmentList.at(0).toElement();
		if (!assignmentTemplate.isNull())
		{
			QDomElement assignmentsElement=assignmentTemplate.parentNode().toElement();
			QListIterator< QMap<QString,QVariant> > i(m_tickets);
			while (i.hasNext())
			{
				QMap<QString,QVariant> ticket= i.next();
				QString owner=ticket[ticket_owner].toString();
				createAssignmentElement(ticket[ticket_id].toInt(),m_owners.indexOf(owner)+1, 
										ticket[ticket_duration].toInt(),assignmentsElement,assignmentTemplate );
				
			}
			//Удалим шаблонную связь
			assignmentsElement.removeChild(assignmentTemplate);
		}
	}

	
	
	
	return dom.toString();
}





QList<int> CProjectXml::getLostTickets()
{
	return m_lostTickets;
}
bool CProjectXml::loadTicketsFromXml(const QString& a_fileName )
{
	// Считаем из файла DOom
	QFile file(a_fileName);
	if (!file.open(QIODevice::ReadOnly))
	{
		qDebug() << "Can't open file " <<a_fileName;
		return false;
	}
	QDomDocument doc;
	if (!doc.setContent(&file)) {
		file.close();
		qDebug() << "Can't parse file " <<a_fileName;
		return false;
	}
	file.close();

	// Разбор тасков
	QDomNodeList taskList=doc.elementsByTagName(xml_Task);
	m_tickets.clear();
	for (int i=0;i<taskList.count();i++)
	{
		QDomElement task=taskList.at(i).toElement();
		QMap<QString,QVariant> m=getTicketFromTask(task);
		m_tickets.append(m);
	}

	// Разбор ресурсов
	QDomNodeList resList=doc.elementsByTagName(xml_Resource);
	m_resources.clear();
	for (int i=0;i<resList.count();i++)
	{
		QDomElement res=resList.at(i).toElement();
		QPair<int,QString> p=getResource(res);
		m_resources.insert(p.first,p.second);
	}

	// Разбор связей ресурсов и тасков
	QDomNodeList resLinkList=doc.elementsByTagName(xml_Assignment);
	for (int i=0;i<resLinkList.count();i++)
	{
		QDomElement res=resLinkList.at(i).toElement();
		linkTicketAndResource(res);
	}


	return true;
}
QList<QMap<QString,QVariant> > CProjectXml::getTickets()
{
	return m_tickets;
}


QMap<QString,QVariant> CProjectXml::ticketFromVariant( QVariant a_ticket )
{
	QMap<QString,QVariant> res;
	QMap<QString,QVariant> empty;
	int type=a_ticket.type();

	// Кажддый тикет - список из 4х элементов 1 - id, последний нужные нам данные 
	if (!a_ticket.canConvert(QVariant::List) )
	{
		qDebug() << "Ticket item is not a list. Ticket value="   << a_ticket;
		return empty;
	}	
	QVariantList l=a_ticket.toList();
	if (!checkFields(l) )
		return empty;
	
	res[ticket_id]=l[0].toInt();
	res[ticket_summary]=l[3].toMap()[ticket_summary];
	res[ticket_description]=l[3].toMap()[ticket_description];
	res[ticket_due_assign]=l[3].toMap()[ticket_due_assign];
	res[ticket_duration]=l[3].toMap()[ticket_duration];
	res[ticket_component]=l[3].toMap()[ticket_component];
	res[ticket_owner]=l[3].toMap()[ticket_owner];
	res[ticket_complete]=l[3].toMap()[ticket_complete].toInt();
	
	return res;

}

bool CProjectXml::checkFields( QVariantList a_ticket )
{
	// Кажддый тикет - список из 4х элементов 1 - id, последний нужные нам данные 
	if (a_ticket.count()<4)
	{
		qDebug() << "Unknown ticket format";
		return false;
	}
	if (!a_ticket[0].canConvert(QVariant::Int))
	{
		qDebug() << "Can't parse id";
	}

	if (!a_ticket[3].canConvert(QVariant::Map))
	{
		qDebug() << "Can't find ticket hash in " << a_ticket;
		return false;
	}
	
	QVariantMap m=a_ticket[3].toMap();


	if (!m.contains(ticket_component) )
	{
		qDebug() << "Can't find " << ticket_component << " in " << m;
		return false;
	}

	if (!m.contains(ticket_summary) )
	{
		qDebug() << "Can't find " << ticket_summary << " in " << m;
		return false;
	}

	// due_assing может и не иметь место 
	//if (!m.contains(ticket_due_assign) )
	//{
	//	qDebug() << "Can't find " << ticket_due_assign << " in " << m;
	//	return false;
	//}

	// Шайтан и это поле может не возвращаться
	//if (!m.contains(ticket_duration) )
	//{
	//	qDebug() << "Can't find " << ticket_duration << " in " << m;
	//	return false;
	//}

	if (!m.contains(ticket_owner) )
	{
		qDebug() << "Can't find " << ticket_owner << " in " << m;
		return false;
	}

	// Да и этого параметра может и не быть
	//if (!m.contains(ticket_complete) )
	//{
	//	qDebug() << "Can't find " << ticket_complete << " in " << m;
	//	return false;
	//}

	return true;
}



bool CProjectXml::checkForLostTickets()
{
	// Проверим нет ли тикета в предшественниках которого есть тикет который не пришел с сервера 
	// Например, мы запросили owner=eross, и один из тикетов имет в предшественниках 
	m_lostTickets.clear();
	bool res=false;
	QListIterator<QMap <QString,QVariant> > ticketsIterator(m_tickets);
	while(ticketsIterator.hasNext())
	{
		QMap<QString,QVariant> t=ticketsIterator.next();
		QList<int> links=idsString2IntList(t[ticket_due_assign].toString());
		QListIterator<int> i(links);
		while(i.hasNext())
		{
			int id=i.next();
			if (!isContainsTicket(id))
			{
				m_lostTickets.append(id);
				qDebug() << "Ticket with id=" << t[ticket_id].toInt() << "links to not exist ticket with id=" << id;
			}
		}
	}
	return m_lostTickets.count();
	
	
}


void CProjectXml::createTaskElement( QMap<QString,QVariant> a_ticket, QDomElement a_parent,QDomElement a_template )
{
	QDomDocument doc=a_template.ownerDocument();
	QDomElement task=a_template.cloneNode().toElement();
	
	replaceNode(task,xml_summary,a_ticket[ticket_summary].toString());
	replaceNode(task,xml_UID,a_ticket[ticket_id].toString());
	replaceNode(task,xml_description,QString("#%1").arg(a_ticket[ticket_id].toString())+"\n"+
		a_ticket[ticket_description].toString());

	QString hourDuration=QString("PT%1H0M0S").arg(a_ticket[ticket_duration].toInt() );
	replaceNode(task,xml_duration,hourDuration);

	double act= a_ticket[ticket_duration].toInt()* ( (double) a_ticket[ticket_complete].toInt()/100);

//	if ( a_ticket[ticket_complete].toInt() == 100 ) //  Пока не разобрался с процентом выполнения ActualWork как-то стремно перехреначивает таск
//		replaceNode(task,xml_actualWork,QString("PT%1H0M0S").arg((int)act));
	

	// Самый геморой начало проекта надо отделить абсолютную дату старта от относительной
	QString start=a_ticket[ticket_due_assign].toString();
	QDomElement prevXmlElement=task.firstChildElement(xml_predecessorLink); // В шаблоне живет ссылка на предшествующие тикеты , поэтому надо эту сылку либо заменить либо удалить
	if (prevXmlElement.isNull())
	{
		qDebug() << "Error in Template. Can't find tag PredecessorLink";
		return;
	}

	QList<int> prevs=idsString2IntList(start); // Найдем все Id предшествующих тикетов
	if (prevs.isEmpty())
	{
		QDate d=QDate::fromString(start,"yyyy/MM/dd");
		if ( d.isValid())
		{
			replaceNode(task,xml_due_assign,d.toString(Qt::ISODate) );
			replaceNode(task,xml_constraintdate,d.toString(Qt::ISODate) );
		}
		else
		{
			replaceNode(task,xml_due_assign,QDateTime::currentDateTime().toString(Qt::ISODate) );
			replaceNode(task,xml_constraintdate,QDateTime::currentDateTime().toString(Qt::ISODate) );
		}
		
	}
	else
	{
		QListIterator<int> i(prevs);
		while(i.hasNext())
		{
			int id =i.next();
			if (isContainsTicket(id))
			{
				QDomElement newprevXmlElement=prevXmlElement.cloneNode().toElement();
				replaceNode(newprevXmlElement,xml_predecessorUID,QString("%1").arg(id) );
				prevXmlElement.parentNode().appendChild(newprevXmlElement);
			}
			else
				replaceNode(task,xml_due_assign,QDateTime::currentDateTime().toString(Qt::ISODate) );
		}
	}

	task.removeChild(prevXmlElement);
	a_parent.appendChild(task);
}




void CProjectXml::createResourceElement( QString a_owner,int a_recourceId, QDomElement a_parent,QDomElement a_template )
{
	QDomDocument doc=a_template.ownerDocument();
	QDomElement resource=a_template.cloneNode().toElement();
	replaceNode(resource,xml_summary,a_owner);
	replaceNode(resource,xml_UID,QString("%1").arg(a_recourceId ) );
	a_parent.appendChild(resource);
}



void CProjectXml::createAssignmentElement(int a_taskId,int a_resId,int a_duration,QDomElement a_parent,QDomElement a_template)
{
	QDomDocument doc=a_template.ownerDocument();
	QDomElement assigment=a_template.cloneNode().toElement();
	replaceNode(assigment,xml_TaskUID,QString("%1").arg(a_taskId));
	replaceNode(assigment,xml_ResourceUID,QString("%1").arg(a_resId ) );
	replaceNode(assigment,xml_RemainingWork,QString("PT%1H0M0S").arg(a_duration ) );
	replaceNode(assigment,xml_UID,QString("%1").arg(a_taskId ) );
	a_parent.appendChild(assigment);	
}

void CProjectXml::replaceNode( QDomElement a_task,QString a_xmlName,QString a_value )
{
	QDomDocument doc=a_task.ownerDocument();
	QDomElement name=doc.createElement(a_xmlName);
	QDomText t = doc.createTextNode(a_value);
	name.appendChild(t);
	QDomNode oldName=a_task.firstChildElement(a_xmlName);
	a_task.replaceChild(name,oldName);
	
}

bool CProjectXml::isContainsTicket( int a_id )
{
	bool res=false;
	QListIterator<QMap <QString,QVariant> > i(m_tickets);
	while(i.hasNext())
	{
		if ( i.next()[ticket_id].toInt()==a_id)
		{
			res=true;
			break;
		}
	}
	return res;
}

QList<int> CProjectXml::idsString2IntList( const QString & a_ids )
{
	QList<int> prevIds;
	if (a_ids.contains("#"))
	{
		QStringList prevs=a_ids.split("#");
		QStringListIterator i(prevs);
		while (i.hasNext() )
		{
			int id=i.next().toInt();
			if (id) // Номер тикета не может быть нулевым 
				prevIds.append(id);
		}
	}
	return prevIds;
}

QStringList CProjectXml::getOwners( const QList<QMap<QString,QVariant> > & a_tickets )
{
	QSet<QString> res;
	QListIterator <QMap<QString,QVariant>> i(a_tickets);
	while (i.hasNext())
	{
		QMap<QString,QVariant> ticket=i.next();
		if (!ticket.contains(ticket_owner))
			qDebug() << "Can't find " << ticket_owner << " in \n"   << ticket;
		else
			if (!ticket[ticket_owner].toString().isEmpty())
				res.insert(ticket[ticket_owner].toString());
	}
	return res.toList();
}

QMap<QString,QVariant> CProjectXml::getTicketFromTask( QDomElement a_task )
{
	QMap<QString,QVariant> res;
	QDomElement el= a_task.firstChildElement(xml_UID);
	//ID
	if(!el.isNull())
	{
		int id =el.text().toInt();
		res.insert(ticket_id,id);
		if (id==0)
			qDebug() << "Parse error: id " << el.text() << "isn't integer ";
	}

	//Summary
	el= a_task.firstChildElement(xml_summary);
	if(!el.isNull())
	{
		res.insert(ticket_summary,el.text());
		if (el.text().isEmpty())
			qDebug() << "Parse warning: summery is empty ";
	}


	//Duration
	el= a_task.firstChildElement(xml_duration);
	if(!el.isNull())
	{
		QString h=el.text();
		// Поскольку у нас в тасках четко прописано, что формат длительности работ в в тасках это час то мы смело можем тут ожидать что-нить типа PT8H0M0S
		// а значит можно тупо выкинуть все лишнее
		h.remove("PT"); 
		h.remove("H0M0S");
		int dur=h.toInt();
		res.insert(ticket_duration,dur);
 		if (dur==0)
			qDebug() << "Parse warning: duration is 0 ";
	}
	
	//предшественники таска и дата старта
	QDomNodeList preList=a_task.elementsByTagName(xml_predecessorUID);
	QString preString;
	for (int i=0;i<preList.count();i++)
	{
		QDomElement pre=preList.at(i).toElement();
		/*QDomElement el= a_task.firstChildElement(xml_predecessorUID);*/
		if(!pre.isNull())
		{
			int id =pre.text().toInt();
			if (id==0)
				qDebug() << "Parse error: id " << el.text() << "isn't integer ";
			else
				preString+="#"+QString("%1").arg(id)+" ";
		}
	}
	if (!preString.isEmpty())
		res.insert(ticket_due_assign,preString);
	else
	{
		el= a_task.firstChildElement(xml_due_assign);
		if(!el.isNull())
		{
			QString dateStr=el.text();
			int t=dateStr.indexOf("T"); 
			dateStr.truncate(t);
			QDate date=QDate::fromString(dateStr,Qt::ISODate);
			dateStr=date.toString("yyyy/MM/dd");
			res.insert(ticket_due_assign,dateStr); 
		}
	}
	return res;
}

QPair<int, QString> CProjectXml::getResource( QDomElement a_task )
{
	QDomElement el= a_task.firstChildElement(xml_UID);
	//ID
	int id =0;
	if(!el.isNull())
	{
		id =el.text().toInt();
		if (id==0)
			qDebug() << "Parse resource error: id " << el.text() << "isn't integer ";
	}
	QString name;

	el= a_task.firstChildElement(xml_summary);
	if(!el.isNull())
	{
		name= el.text();
		if (el.text().isEmpty())
			qDebug() << "Parse resource warning: name is empty ";
	}
	return QPair<int,QString>(id,name);


}

void CProjectXml::linkTicketAndResource( QDomElement a_link )
{
	
	QDomElement el= a_link.firstChildElement(xml_TaskUID);
	int taskId =0;
	if(!el.isNull())
	{
		taskId =el.text().toInt();
		if (taskId==0)
			qDebug() << "Parse resource link error: id " << el.text() << "isn't integer ";
	}
	
	el= a_link.firstChildElement(xml_ResourceUID);
	int resId =0;
	if(!el.isNull())
	{
		resId =el.text().toInt();
		if (resId==0)
			qDebug() << "Parse resource link error: id " << el.text() << "isn't integer ";
	}
	// Найдем нужный тикет
	for (int i=0; i<m_tickets.count();i++)
	{
		if ( m_tickets[i][ticket_id].toInt() == taskId )
		{
			if (m_resources.contains(resId))
				m_tickets[i][ticket_owner]=m_resources[resId];
			else
				qDebug() << "Parse resource link error: can't find resource with id=" << resId;
		}
	}

}