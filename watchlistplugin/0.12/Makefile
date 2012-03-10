all:

install:
	sudo easy_install .

setup:
	python ./setup.py compile_catalog
	sudo python setup.py develop --exclude-scripts; sudo chown ${USER} . -R

messages:
	python ./setup.py extract_messages
	python ./setup.py update_catalog
	python ./setup.py compile_catalog

upload:
	python setup.py bdist_egg upload

minify:
	yuicompressfile tracwatchlist/htdocs/js/*.js tracwatchlist/htdocs/css/*.css

clean:
	sudo rm -rf build dist temp TracWatchlistPlugin.egg*

dep:
	python setup.py --command-packages=stdeb.command bdist_deb
