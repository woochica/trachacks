default: dist/scrum-1.0.0-py2.4.egg

dist/scrum-1.0.0-py2.4.egg : scrumplugin/htdocs/ProjectCharts.class
		python setup.py bdist_egg

scrumplugin/htdocs/ProjectCharts.class : scrumplugin/htdocs/ProjectCharts.java
		cd scrumplugin/htdocs && \
		javac -Xlint:deprecation -classpath jfreechart-1.0.3.jar;jcommon-1.0.6.jar ProjectCharts.java && \
		cd ../..    

install : dist/scrum-1.0.0-py2.4.egg
		python setup.py install
