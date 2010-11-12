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
        'ripe': extractors,
    }
except ImportError:
    pass

setup(
    name = 'TracReportInplaceEditPlugin',
    version = "0.1",
    description = "Edit tickets in reports by inplace editor",
    author = "Richard Liao",
    author_email = "richard.liao.i@gmail.com",
    url = "http://trac-hacks.org/wiki/TracReportInplaceEditPlugin",
    license = "BSD",
    packages = find_packages(exclude=['ez_setup', 'examples', 'tests*']),
    include_package_data = True,
    package_data = { 'ripe': [ '*.txt', 'templates/*.*', 'htdocs/*.*', 
        'tests/*.*', 'locale/*.*', 'locale/*/LC_MESSAGES/*.*' ] },
    zip_safe = False,
    keywords = "trac TracReportInplaceEditPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    install_requires = [],
    entry_points = """
    [trac.plugins]
    ripe = ripe.web_ui
    """,
    **extra
    )

