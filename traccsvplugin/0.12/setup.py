from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='TracCsvPlugin',
    version = '0.0.1',
    author = 'Bangyou Zheng',
    author_email = '',
    description = 'A IHTMLPreviewRenderer for CSV file',
    license = "BSD",
    url = 'http://trac-hacks.org/wiki/TracCsvPlugin',
    packages=find_packages(exclude=['*.tests*']),
    package_data = { 'csvplugin': ['htdocs/*.js','htdocs/*.css','htdocs/*.gif'] },
    entry_points = {
        'trac.plugins': [
            'csvplugin = csvplugin.render'
        ]
    }
)
