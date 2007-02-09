from setuptools import setup, find_packages
#setup(
#    name = "sprintReports",
#    version = "0.1",
#    packages = find_packages(),
#)


from setuptools import setup, find_packages

PACKAGE = 'testManagementPlugin'
VERSION = '0.0.2'

setup(
    name=PACKAGE, version=VERSION,
    description='test case management tool',
    author="edunne", author_email="eoin.dunne@divestco.com",
    license='BSD', url='http://www.trac-hacks.org/wiki/TestCaseManagementPlugin',
    packages=['testManagementPlugin'],
    package_data={
        'testManagementPlugin': [
            'htdocs/css/*.css',
            'templates/*.cs',
            'htdocs/img/*.png',
            'htdocs/js/*.js'
        ]
    },
    entry_points= {
        'trac.plugins' : [
         'testManagement=testManagementPlugin.testManager',
         'manageTestRuns=testManagementPlugin.testRuns',
         'testRunResults=testManagementPlugin.testResults'
        ]
    },
)


#package_data={
    #    'webadmin': [
    #        'htdocs/css/*.css',
    #        'htdocs/img/*.png',
    #        'htdocs/js/*.js',
    #        'templates/*.cs'
    #    ]
    #},
    #entry_points = {
    #    'trac.plugins': [
    #        'webadmin.web_ui = webadmin.web_ui',
    #        'webadmin.basics = webadmin.basics',
    #        'webadmin.logging = webadmin.logging',
    #        'webadmin.perm = webadmin.perm',
    #        'webadmin.plugin = webadmin.plugin',
    #        'webadmin.ticket = webadmin.ticket'
    #    ]
    