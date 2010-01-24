#ifndef PROJECTXML_H
#define PROJECTXML_H

#include <QObject>
#include <QVariantList>
#include <QDomDocument>

#define ticket_id "id"
#define ticket_component "component"
#define ticket_summary "summary"
#define ticket_description "description"
#define ticket_duration "duration"
#define ticket_due_assign "due_assign"
#define ticket_owner "owner"
#define ticket_complete "complete"


class CProjectXml : public QObject
{
	Q_OBJECT

public:
	CProjectXml(QObject *parent=0);
	~CProjectXml();

	/**
	 * @brief Установить тикеты
	 *
	 * В каждом элементе из списка проверяется наличае необходимых полей у тикета
	 * @param a_tickets список тикетов 
	 * @return true если все тикеты прошли проверку
	 */
	bool loadTicketsFromVariantList(QVariantList a_tickets);

	/**
	 * @brief Преобразовать тикеты , установленные ранее через setTickets в xml, понятный MS Project
	 */
	QString getXmlFromTickets();

	/**
	 * @brief Получить список Id тикетов которых не хватает (тикеты на которые ссылаются другие)
	 *
	 * @returns список id
	 */
	QList<int> getLostTickets();

	/**
	 * @brief Загрузить xml файл и попытаться преобразовать его в список тикетов, который потом можно будет получить с помощью 
	 *
	 *
	 * @param a_fileName имя xml
	 * @return 
	 */
	bool loadTicketsFromXml(const QString& a_fileName);

	
	/**
	 * @brief Список тикетов 
	 *
	 * QMap<название поля,значение>
	 * @return 
	 */
	QList<QMap<QString,QVariant> > getTickets();
	

private:
	QList<QVariantMap > m_tickets;			///< Тикеты, уже проверенные на наличае важных полей
	QList<QString> m_owners;							///< Список пользователей (ресурсов) последовательность в списке существенна. положение в этом списке +1 = идентификатор в xml ке. (+1 потому, что 0 элемент Ms Project не воспринимает), используется при передаче данных в Project
	QMap <int, QString> m_resources;					///< Список ресурсов вычитанных в xml (см. getResource). используется при передаче данных из Project(а)
	QDomDocument m_template;							///< Шаблон на основании которого будем кписать сой xml (я ленивая жопа)
	QList<int> m_lostTickets;							///< Список тикетов на которые ссылаются другие но которые не вошли в выборку полученную с сервера

	/**
	 * @brief конвертация тикета в виде QVariant в QMap
	 *
	 * Проверяется наличие важных полей 
	 * @param a_ticket тикет в QVariant
	 * @return  в случае ошибки пустой map
	 */
	QMap<QString,QVariant> ticketFromVariant(QVariant a_ticket);

	/**
	 * @brief Проверка на наличие нужных полей в одном тикете
	 *
	 *
	 * @param a_ticket тикет
	 * @return  true если что все нужно есть 
	 */
	bool checkFields(QVariantList a_ticket);

	/**
	 * @brief Провериьт нет ли ссылок на несуществующие тикеты
	 *
	 * @returns true если есть
	 */
	bool checkForLostTickets();

	/**
	 * @brief Добавление в Dom модель тикета 
	 *
	 * @param a_ticket тикет (такс согласно формату MS Project)
	 * @param a_parent элемент "Tasks"
	 * @param a_template Шаблон для создания Task(f)
	 * @returns void
	 */
	void createTaskElement(QMap<QString,QVariant> a_ticket, QDomElement a_parent,QDomElement a_template);

	/**
	* @brief Добавление в Dom модель тикета 
	*
	* @param a_owner имя Owner(a) (ресурса)
	* @param a_resourceId Идентификатор ресурса (нужен для того, что бы таски могли ссылаться на свои ресерсы)
	* @param a_parent элемент "Resource"
	* @param a_template Шаблон для создания Task(a)
	* @returns void
	*/
	void createResourceElement(QString a_owner,int a_recourceId, QDomElement a_parent,QDomElement a_template);

	/**
	 * @brief Добавление в Dom модель связи задачи и исполнителя
	 *
	 *
	 * @param a_taskId идентификатор задачи в  xml
	 * @param a_resId индентификатор ресурса в xml
	 * @param a_duration длительность задачи
	 * @param a_parent элемент "Assignment"
	 * @param a_template Шаблон для создания Assignment(a)
	 * @return 
	 */
	void createAssignmentElement(int a_taskId,int a_resId,int a_duration,QDomElement a_parent,QDomElement a_template);
	/**
	 * @brief Заменить в таске знаечние элемента на значение из тикета
	 *
	 * @param a_task Элемент (таск),в  котором надо поменять знаение тега (не обязательно такс может быть просто тег внутри которого надо произвести замену)
	 * @param a_xmlName имя тега 
	 * @param a_value Новое значение
	 */
	void replaceNode(QDomElement a_task,QString a_xmlName,QString a_value);

	/**
	 * @brief  Проверка есть ли среди тикетов тикет с заданным Id
	 *
	 * Используется для проверки зависимых тикетов (нельзя ссылаться на тикет, которого нет)
	 * @param a_id искомый Id
	 * @returns true - тикет присутсвует
	 */
	bool isContainsTicket(int a_id);

	/**
	 * @brief Преобразование из строки "#15 #18 #19" в список int(ов) 
	 *
	 * @param a_ids исходная строка
	 * @returns список целочисленных значений
	 */
	QList<int> idsString2IntList(const QString & a_ids);


	/**
	 * @brief Вытащить из тикетов всех пользователей  
	 *
	 *
	 * @param a_tickets тикеты
	 * @return список владельце тикетов (тех кто их будет делать, не путать с репортерами) 
	 */
	QStringList getOwners(const QList<QMap<QString,QVariant> > & a_tickets);

	/**
	 * @brief Распарсить таск из dom элемента
	 *
	 *
	 * @param a_task элемент таска
	 * @return QMap<название свойства, Занчение> 
	 */
	QMap<QString,QVariant> getTicketFromTask(QDomElement a_task);

	/**
	 * @brief Получить информаци о ресурсе из dom элемента
	 *
	 * @param a_res элемент для ресурса
	 * @returns QPair<UID ресурса, имя ресурса>  
	 */
	QPair<int, QString> getResource(QDomElement a_res);

	/**
	 * @brief Проставить в тикет владельца 
	 *
	 * @param a_link dom элемент связи тикета и владельца
	 * @returns void
	 */
	void linkTicketAndResource(QDomElement a_link);

	
		
};

#endif // PROJECTXML_H
