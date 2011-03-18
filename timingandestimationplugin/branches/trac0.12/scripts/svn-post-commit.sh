#!/bin/bash
log() {
    while read data
    do
	echo "[$(date +'%T')] $data" | tee -a $LOG || continue
    done
}

set -e
REPOS="$1"
REV="$2"
CNAME=`basename "$REPOS"`
export LOGDIR="/var/log/commit-hooks"
LOG="${LOGDIR}/$CNAME.svn-post-commit.log"
mkdir -p "${LOGDIR}"

echo "`date +'%F'` in svn post commit : $REPOS : $REV" | log
MESSAGE=`svnlook log -r $REV $REPOS`
AUTHOR=`svnlook author -r $REV $REPOS`

if [ -z "$TRAC_ENV" ] && [ -e "/var/trac/$CNAME" ]; then
    export TRAC_ENV="/var/trac/$CNAME"
fi

echo "TracEnv:$TRAC_ENV Repo:$REPOS Rev:$REV Auth:$AUTHOR" | log

/usr/bin/python /var/trac/trac-post-commit.py -p "$TRAC_ENV" -r "$REV" -u "$AUTHOR" -m "$MESSAGE" 2>&1 | log

