
VERSION=$(TRAC)
PATH:=$(PATH):/opt/trac/$(VERSION)/bin/
ENV=/home/roman/Trac

all:
	- killall tracd
	python setup.py clean bdist_egg
	cp ./dist/*.egg ~/Trac/$(VERSION)/plugins
	export PATH=$(PATH); tracd -p 8081 --auth="$(VERSION),./.htdigest,trac" $(ENV)/$(VERSION)/ &

stop:
	- killall tracd
