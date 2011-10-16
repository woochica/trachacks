egg:
	cd .. && python setup.py --quiet bdist_egg

deploy:
	cp ../dist/*.egg /var/lib/trac/coclico/plugins/ && sudo apache2ctl graceful
