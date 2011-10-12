egg:
	cd .. && python setup.py --quiet bdist_egg

deploy:
	cp ../dist/*.egg ../../.. && sudo apache2ctl graceful
