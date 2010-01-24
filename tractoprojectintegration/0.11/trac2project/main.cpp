#include <QtGui/QApplication>
#include "trac2project.h"

int main(int argc, char *argv[])
{
	QApplication a(argc, argv);
	CTrac2xml w;
	w.show();
	return a.exec();
}
