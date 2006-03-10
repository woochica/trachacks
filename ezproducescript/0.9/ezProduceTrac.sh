#!/bin/sh
PREFIX=
SVN_HOME=/opt/svn
POSTGRES_HOME=/opt/postgresql
TRAC_HOME=/opt/trac
SVN_REPOS_ROOT=/data/svnrepos
TRAC_PROJECT_ROOT=/home/projects

WHOAMI=`/usr/bin/whoami`
if [ $WHOAMI != "root" ]; then
	echo "You must be root to add new trac-project!"
	exit 1
fi

# show current projects list
echo ""
echo "Curretn Projects list: "
ls -l $SVN_REPOS_ROOT


case $1 in
	add)
	# input project name
	   echo -n "Project name: "
	   read PROJECTNAME
	# check exists project corrision
           if [ -e $TRAC_PROJECT_ROOT/$PREFIX$PROJECTNAME/README ];
           then
                   echo ""
                   echo "already exists project name : $PREFIX$PROJECTNAME."
                   exit 1
           fi


           echo "Adding trac project: $PREFIX$PROJECTNAME."
	# create metadata db
           echo "Create DB $PREFIX$PROJECTNAME."
           su - postgres -c "$POSTGRES_HOME/bin/createdb $PREFIX$PROJECTNAME 'Database for trac project $PROJECTNAME'";
           echo "created."
	# create repos
           echo "Create subverion repos $PREFIX$PROJECTNAME."
           $SVN_HOME/bin/svnadmin create $SVN_REPOS_ROOT/$PREFIX$PROJECTNAME;
           echo "created."
	# create project dir
           echo "Create trac project $PREFIX$PROJECTNAME."
           $TRAC_HOME/bin/trac-admin $TRAC_PROJECT_ROOT/$PREFIX$PROJECTNAME initenv $PREFIX$PROJECTNAME \
           postgres://trac:trac@localhost/$PREFIX$PROJECTNAME \
           $SVN_REPOS_ROOT/$PREFIX$PROJECTNAME \
           $TRAC_HOME/share/trac/templates;
           echo "created."
	# chmod project data dir permission
           echo "Setup misc.."
           chmod 777 $TRAC_PROJECT_ROOT/$PREFIX$PROJECTNAME
           chmod 777 $TRAC_PROJECT_ROOT/$PREFIX$PROJECTNAME/log
           chmod 777 $TRAC_PROJECT_ROOT/$PREFIX$PROJECTNAME/plugins
           echo "Setup finish."
	   ;;
	del)
	# input project name
	   echo -n "Project name: "
	   read PROJECTNAME
	# check exists project name
           if [ ! -e $TRAC_PROJECT_ROOT/$PROJECTNAME/README ];
           then
                   echo "" 
                   echo "Coudn't find project : $PROJECTNAME."
                   exit 1
           fi


           echo "Removing trac project: $PROJECTNAME."
	# drop metadata db
           echo "Drop DB $PROJECTNAME."
           su - postgres -c "$POSTGRES_HOME/bin/dropdb $PROJECTNAME";
           echo "droped."
	# delete repos
           echo "Delete subverion repos $PROJECTNAME."
           rm -rf $SVN_REPOS_ROOT/$PROJECTNAME;
           echo "deleted."
	# delete project dir
           echo "Delete trac project $PROJECTNAME."
           rm -rf $TRAC_PROJECT_ROOT/$PROJECTNAME
           echo "deleted."
	   ;;
	*)
	   echo ""
	   echo "    useage: ./ezProduceTrac.sh [ add | del ]"
	   echo ""
	   ;;
esac
exit 1

