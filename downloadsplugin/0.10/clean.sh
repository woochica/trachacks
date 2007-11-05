#!/bin/bash

QUERY="DROP TABLE download; \
  DROP TABLE architecture; \
  DROP TABLE platform; \
  DROP TABLE download_type; \
  DELETE FROM system WHERE name = 'downloads_description'; \
  DELETE FROM system WHERE name = 'downloads_version';"

echo $QUERY | sqlite3 $1/db/trac.db
