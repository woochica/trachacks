
VERSION=$(TRAC)
PYTHONPATH:=/opt/trac/$(VERSION)/lib/python2.7/site-packages/
PATH:=$(PATH):/opt/trac/$(VERSION)/bin/
ENV=/home/roman/Trac

all:
	- killall tracd
	python setup.py clean bdist_egg
	cp ./dist/*.egg ~/Trac/$(VERSION)/plugins
	export PATH=$(PATH); export PYTHONPATH=$(PYTHONPATH); tracd -p 8080 --auth="$(VERSION),$(ENV)/htdigest,trac" $(ENV)/$(VERSION)/ &

stop:
	- killall tracd
