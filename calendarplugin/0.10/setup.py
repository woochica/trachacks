# -*-coding:utf-8-*-
from setuptools import setup

setup(
    name = 'AztechCalendar',
    version = '0.1',
    packages = ['azcalendar'],
    package_data = {
        'azcalendar': [
            'templates/*.cs',
            'htdocs/images/*.jpg',
            'htdocs/css/*.css',
            'templates/*.cs'
        ]
    },

    description = 'Calendar for Trac',
    author = 'Petr Machata, Jiří Moskovčák',
    author_email = 'pmachata@gmail.com',
    license = 'BSD',
    keywords = 'trac calendar',
    url = 'http://www.trac-hacks.org/wiki/CalendarPlugin',

    entry_points = {
        'trac.plugins': [
            'azcalendar.azcalendar = azcalendar.azcalendar'
        ]
    }
)
