# For licensing and copyright info, see multicommitupdater/commitupdater.py
from setuptools import setup

setup(name='MultiProjectCommitTicketUpdater',
      version='0.12.1',
      description='Multi-project version of commit_updater',
      author='fleeblewidget',
      author_email='fleeblewidget@gmail.com',
      packages=['multicommitupdater'],
      entry_points = {
        'trac.plugins': [
            'multiprojectcommitticketupdater = multicommitupdater.commitupdater',
            ],
        },
      )
