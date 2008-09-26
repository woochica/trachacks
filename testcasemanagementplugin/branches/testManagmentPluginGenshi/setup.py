from setuptools import find_packages, setup

setup(
    name='testManagementPlugin', version='0.11.3',
    author="Eoin Dunne", author_email="edunnesoftwaretesting@hotmail.com",
    license='BSD', url='http://www.trac-hacks.org/wiki/TestCaseManagementPlugin',
    packages=['testManagementPlugin'],
    package_data={
        'testManagementPlugin': [
            'htdocs/css/*.css',
            'templates/*.html',
            'htdocs/img/*.png',
            'htdocs/js/*.js'
        ]
    },
    entry_points= {
        'trac.plugins' : [
         'testManagement=testManagementPlugin.testManager',
         'manageTestRuns=testManagementPlugin.testRuns',
         'testRunResults=testManagementPlugin.testResults',
         'setPathForTestcases=testManagementPlugin.pathManager',
         'validateTestRun=testManagementPlugin.testScriptValidator'
        ]
    },
)
    