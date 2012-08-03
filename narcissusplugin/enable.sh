#!/bin/bash
ABS="/usr/other/ugsvn/tracenvs"
AUTH="/usr/other/ugsvn/groups.d"
EMAIL="@ug.it.usyd.edu.au"

confx="$1/conf/trac.ini"
confy="$ABS/$confx"

frag="trac.ini.fragment.txt"

if [ ! -r "$frag" ] ; then
  echo "Can't read '$frag'"
  exit 1
fi

if [ -w "$confy" ] ; then
  conf="$confy"
  env="$ABS/$1"
elif [ -w "$confx" ] ; then
  conf="$confx"
  env="$1"
else
  echo "Can't find or no write permissions for trac.ini"
  echo "Tried '$confx' and '$confy'"
  echo "Usage: $0 tracenv"
  exit 1
fi

tracdb="$env/db/trac.db"
gid=`basename "$env"`
gpath="$AUTH/$gid"
if [ ! -r "$gpath" ] ; then
  echo "Can't read '$gpath'"
  exit 1
fi

if [ ! -w "$tracdb" ] ; then
  echo "Can't write to '$tracdb'"
  exit 1
fi

echo "Group members:"
for i in `cat "$gpath"` ; do
  name=`grep "^${i}:" /etc/passwd | cut -f5 -d: | cut -f1 -d,`
  echo -e "$i     \t$i$EMAIL   \t$name"
done

echo -n "Proceed [n/Y]? "
read y
if [[ $y == n* || $y == N* ]] ; then
  exit 1
fi

for i in `cat "$gpath"` ; do
  name=`grep "^${i}:" /etc/passwd | cut -f5 -d: | cut -f1 -d,`
  echo "INSERT INTO session_attribute VALUES('$i', 1, 'name', '$name');" | tee /dev/stderr | sqlite3 $tracdb 
  echo "INSERT INTO session_attribute VALUES('$i', 1, 'email', '${i}${EMAIL}');" | tee /dev/stderr | sqlite3 $tracdb 

  # this next one allows the user to show up as a ticket assignee when restrict_owner is true
  echo "INSERT INTO session VALUES('$i', 1, 1204623330);" | tee /dev/stderr | sqlite3 $tracdb

  echo "INSERT INTO narcissus_settings VALUES('member', '$i');" | tee /dev/stderr | sqlite3 $tracdb
done

if grep '\[components]' "$conf" ; then
  echo "$conf has a [components] section -- needs to be patched with the following:"
  echo "--------------- snip ------------------"
  cat "$frag"
  echo "---------------------------------------"
else
  echo 'cat "'"$frag"'" >> "'"$conf"'"'
  cat "$frag" >> "$conf"
fi

echo 'trac-admin '$env' upgrade'
trac-admin $env upgrade

echo 'trac-admin '$env' permission add authenticated NARCISSUS_VIEW'
trac-admin $env permission add authenticated NARCISSUS_VIEW
if [ $? -ne 0 ] ; then
   echo 'The command to add NARCISSUS_VIEW failed -- probably beacuse narcissus is not in the componenets section yet'
   echo 'After adding narcissus to componenets, you must run: '
   echo -e '\ttrac-admin '$env' permission add authenticated NARCISSUS_VIEW'
   echo -e '\ttrac-admin '$env' upgrade'
fi
