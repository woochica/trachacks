all:

install:
	sudo easy_install .

setup:
	sudo python setup.py develop --exclude-scripts

messages:
	python ./setup.py extract_messages
	python ./setup.py update_catalog

