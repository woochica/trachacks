from setuptools import find_packages, setup

setup(
    name='TypedTicketWorkflow-plugin', version='0.1',
    packages=find_packages(),
    author = 'Vladimir Abramov',
    author_email = 'kivsiak@gmail.com',
    licence = 'BSD',
    description = 'Type - attribute workflow filter for trac ticket',
    long_description = 'Allow to filter actions by \'type\' ticket attribute',
    entry_points = {'trac.plugins':['typedworkflow.controller = typedworkflow.controller']},
)