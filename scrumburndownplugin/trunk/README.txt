Dependencies for testing:
 - Nose (easy_install nose)
 - Nose test config (easy_install nose-testconfig)
 - Coverage (easy_install coverage)

Running tests
  You can run tests by executing the following command in the root of the project:

     python setup.py test


Running tests with coverage

    nosetests --cover-erase --with-coverage
    coverage -r burndown/burndown.py burndown/dbhelper.py
    coverage -a burndown/burndown.py
