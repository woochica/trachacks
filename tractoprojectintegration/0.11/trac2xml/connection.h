#ifndef CONNECTION_H
#define CONNECTION_H

#include <QObject>
#include "xmlrpc/client.h"

class CConnection : public QObject
{
	Q_OBJECT

public:
	CConnection(QObject *parent);
	~CConnection();

	/**
	 * @brief Установить Url куда будут отправляться запросы
	 *
	 * @param a_url  строка с адресом 
	 * @param a_port порт 
	 */
	void setUrl(const QString &  a_url,int a_port);

	/**
	 * @brief Установить логин и пароль для юзера трака от чьего имени будут отправляться запросы
	 *
	 * @param a_login логин
	 * @param a_password пароль
	 * @returns void
	 */
	void setUser(const QString &  a_login,const QString &  a_password);

	/**
	* @brief Запросить с сервера список тикетов 
	*
	* Сначала с сервера приходят Id и испускается сигнал ticketCountRecieved
	* После чего по каждому из id последовательно отправляется запрос requestTicketInfo
	* После получения информации о всех тикетах испускается сигнал ticketsRecieved
	* @param a_request запрос на получение выборки тикетов (напимер status!=closed)
	*/
	void requestTickets(const QString a_requset);

	/**
	* @brief Запросить информацию о тикете 
	*
	* @param a_id идентификатор тикета
	*/
	void requestTicketInfo(int a_id);

	/**
	 * @brief Отправить на сервер запрос на изменение тикетов
	 *
	 * @param a_tickets список тикетов
	 * @returns void
	 */
	void requestForTicketsUpdate(QList<QMap<QString,QVariant> >  a_tickets);

signals:
	/**
	 * @brief С сервера получена вся информация запрошенная в requestTickets 
	 *
	 * @param a_tickets список тикетов и их свойств 
	 */
	void ticketsRecieved(QVariantList a_tickets);

	/**
	 * @brief СИгнал о том что с сервера получен список тикетов 
	 *
	 * @param a_coint число полученных тикетов
	 */
	void ticketCountRecieved(int a_coint);

	/**
	 * @brief Получена информация, запрошенная в requestTicketInfo
	 *
	 * @param a_ticket  тикет ([id, time_created, time_changed, attributes])
	 */
	void ticketInfoRecieved(QVariant a_ticket);


	/**
	 * @brief Получена информация о том что тикет обновлен 
	 *
	 * @returns void
	 */
	void ticketUpdated();

	/**
	 * @brief Процесс обновления тикетов завершен
	 *
	 * @param a_errorTickets список тикетов с ошибками 
	 * @returns void
	 */
	void ticketsUpdated(QList<QMap<QString,QVariant> >  a_errorTickets);


private:
	xmlrpc::Client * m_xmlrpc;							///< xmlrpc  клиент
	int m_ticketListRequest;							///< Идентификатор запроса на получение списка id тикетов
	int m_ticketInfoRequest;							///< Идентификатор запроса на получение информации о тикете
	int m_ticketUpdateRequest;							///< Идентификатор запроса на обновление тикета
	QList<int> m_idsForRequest;							///< Очередь идентификторов тикетов, запрос о которых предстоит отправить на сервер (Работает по FIFO)
	QVariantList m_tickets;								///< Полученные тикеты с подробной информацией 
	QList<QMap<QString,QVariant> >  m_ticketsForUpdate; ///< тикеты, которые надо обновить на сервере
	QList<QMap<QString,QVariant> >  m_errorTickets;		///< список тикетов, которые в процессе обновления поймали на ошибку


	/**
	* @brief Начать запрашивать информацию о всех тикетах 
	*
	*
	* @param a_ids список идентификаторов 
	*/
	void startRequestInfoForAllTickets(QVariant a_ids);


	/**
	 * @brief  Обработчик получения информации о успешном обновлении тикета
	 *
	 * @returns void
	 */
	void onTicketUpdated();
	/**
	* @brief Обработчик получения информации о тикете 
	*
	* Удаляется элемент из m_idsForRequest 
	* @param a_value информация о тикете
	* @return 
	*/
	void onTicketInfoRecieved(QVariant a_value);

	/**
	* @brief Отправить на сервер запрос на изменение тикета
	*
	* @param a_ticket тикет для изменения
	* @returns идентификатор запроса обновления
	*/
	int requestForTicketUpdate(QMap<QString,QVariant> a_ticket);

private slots:
	/**
	* @brief Обработчик положительного ответа сервера
	*
	*
	* @param a_requestId идентификатор запроса
	* @param a_value значение ответа
	* @return 
	*/
	void processReturnValue( int a_requestId, QVariant a_value );

	/**
	* @brief Обработчик ошибки сервера
	*
	*
	* @param a_requestId идентификатор запроса
	* @param a_errorCode код ошибки
	* @param a_errorString Текст ошибки 
	* @return 
	*/
	void processFault( int a_requestId, int a_errorCode, QString a_errorString );

	
};

#endif // CONNECTION_H
