

== Installation ==
# trac als DEB installiert,
apt-get install trac python-mysqldb



==== installieren ====

trac-admin /opt/tracenv initenv 
trac-admin /opt/tracenv permission add anonymous TRAC_ADMIN


==== alles neu aufsetzen ====
rm -rf /opt/tracenv
trac-admin /opt/tracenv initenv DEVTRAC sqlite:db/trac.db  svn /dev/null
trac-admin /opt/tracenv permission add anonymous TRAC_ADMIN
touch /opt/tracenv/htdocs/your_project_logo.png

# set logging 
#sed 's/^log_type\ =\ none/log_type\ =\ stderr/g' /opt/tracenv/conf/trac.ini > /tmp/tracfarm_xslt_tmp && cp /tmp/tracfarm_xslt_tmp /opt/tracenv/conf/trac.ini

# server starten
tracd -p 8000  /opt/tracenv -r -s  

==== config ===
[trac]
auto_reload = true
; 
== starten ==

tracd -p 8000  /opt/tracenv -r -s



== Development ==

cd /path/to/plugin/src
python setup.py develop --multi-version --exclude-scripts --install-dir /path/to/projenv/plugins

# python setup.py develop -mxd /opt/tracenv/plugins

