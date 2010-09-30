from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='TracAjaxQuery', 
    author = 'ragasa',
    version='0.1',
    url = 'http://trac-hacks.org/wiki/TracAjaxQueryPlugin',
    description = 'AJAX style filtering for ticket query when viewing tickets',
    zip_safe = True,
    packages = ['ajaxquery'],
    package_data = {'ajaxquery': ['templates/*.html','htdocs/js/*.js','htdocs/image/*.gif']},
    entry_points = {'trac.plugins': ['ajaxquery = ajaxquery']},
)