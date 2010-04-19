python setup.py bdist_egg
copy dist\jobcontrol-0.1-py2.5.egg c:\work\marketdata\trac-0.11\test\plugins /Y
tracd -p 8000 c:\work\marketdata\trac-0.11\test
