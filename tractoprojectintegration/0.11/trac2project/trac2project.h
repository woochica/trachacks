#ifndef TRAC2XML_H
#define TRAC2XML_H

#include <QtGui/QWidget>
#include "ui_trac2project.h"
#include "connection.h"


class CTrac2xml : public QWidget
{
	Q_OBJECT

public:
	CTrac2xml(QWidget *parent = 0, Qt::WFlags flags = 0);
	~CTrac2xml();


	

private:
	Ui::CTrac2xmlClass m_ui;			///< Тупая Гуйня
	CConnection m_connection;			///< Общение с trac
	QVariantList m_tickets;				///< полученные с сервера тикеты , сюда попадают тикеты при вытягивании зависимостей тикетов
	
private slots:
	void on_m_toTrac_clicked();
	void on_m_createXml_clicked();

	/**
	 * @brief Обрвботик события получения с сервера количества тикетов удовлетворяющих запросу
	 *
	 * @param a_count количество тикетов
	 */
	void onTicketCountRecieved( int a_count);


	/**
	 * @brief Обработчик событий: получения информации о тикете , обновление тикета 
	 *
	 * Используется для инкриментации прогрессбара 
	 */
	void incProgress( );

	/**
	 * @brief Обарботчик события получения всех тикетов
	 *
	 * @param a_tickets список тикетов со всеми свойствами
	 * @returns void
	 */
	void onTicketsRecieved(QVariantList a_tickets);

	/**
	 * @brief  Обаботчик события обновления всех тикетов
	 *
	 * @param a_errorTickets список тикетов с обшибками
	 * @returns void
	 */
	void onTicketsUpdated(QList<QMap<QString,QVariant> >  a_errorTickets);


	/**
	 * @brief Установка и сохранение параметров подключения 
	 *
	 * Данные записываются в ini файл и устанавливаются для m_connection
	 */
	void setConnectInfo();

	/**
	 * @brief Загрузка параметров подключения
	 *
	 * @returns void
	 */
	void loadConnectionInfo();

	/**
	 * @brief Запрос информации о тикетах удовлетворяющих запросу 
	 *
	 * @param a_query запрос (например status!=closed&owner=eross см. get параметры страница Custom Query)
	 * @returns void
	 */
	void requestTickets(const QString &  a_query);
};

#endif // TRAC2XML_H
