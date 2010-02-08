from setuptools import find_packages, setup

extra = {}

try:
    import babel
    extractors = [
        ('**.py',                'python', None),
        ('**/templates/**.html', 'genshi', None),
        ('**/templates/**.js',   'javascript', None),
        ('**/templates/**.txt',  'genshi',
         {'template_class': 'genshi.template:NewTextTemplate'}),
    ]
    extra['message_extractors'] = {
        'tickettemplate': extractors,
    }
except ImportError:
    pass

setup(
    name = 'TracTicketTemplate',
    version = '0.7',
    packages = ['tickettemplate'],
    package_data = { 'tickettemplate': [ '*.txt', 'templates/*.*', 'htdocs/*.*', 
        'tests/*.*', 'locale/*.*', 'locale/*/LC_MESSAGES/*.*' ] },

    author = "Richard Liao",
    author_email = 'richard.liao.i@gmail.com',
    maintainer = 'Richard Liao',
    maintainer_email = "richard.liao.i@gmail.com",
    description = "Ticket template plugin for Trac.",
    license = "BSD",
    keywords = "trac ticket template",
    url = "http://trac-hacks.org/wiki/TracTicketTemplatePlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = [],
    entry_points = {'trac.plugins': ['tickettemplate = tickettemplate.ttadmin']},
    **extra
)
