#!/bin/bash

QUERY="DROP TABLE screenshot; \
  DROP TABLE screenshot_version; \
  DROP TABLE screenshot_component; \
  DELETE FROM system WHERE name = 'screenshots_version';"

echo $QUERY | sqlite3 $1/db/trac.db
