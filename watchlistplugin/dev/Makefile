all:

install:
	sudo easy_install .

setup:
	sudo python setup.py develop --exclude-scripts; sudo chown ${USER} . -R

messages:
	python ./setup.py extract_messages
	python ./setup.py update_catalog
	python ./setup.py compile_catalog

upload:
	python setup.py bdist_egg upload

