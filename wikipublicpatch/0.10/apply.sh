#!/bin/sh

if [ -n "$1" ]; then
	echo "Applying WikiPublic patch..."
	patch -d $1 -p1 < WIKI_PUBLIC.patch
	echo "Making WikiStart page public..."
	patch -d $1 -p1 < WIKISTART_PUBLIC.patch
	echo "Done."
else
	echo "Usage: apply.sh TRACDIR"
fi
