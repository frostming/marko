#!/usr/bin/env bash

set -e

VERSION=$1

if [ -z "$VERSION" ]; then
	echo 'Please give spec version to dump: ./spec.sh $VERSION'
	exit 1
fi

function main {
	echo "Downloading spec file $VERSION..."
	curl "https://raw.githubusercontent.com/commonmark/commonmark-spec/$VERSION/spec.txt" -o spec/commonmark.txt
	# No corresponding tag on GFM spec, use master anyway
	curl "https://raw.githubusercontent.com/github/cmark-gfm/master/test/spec.txt" -o spec/gfm.txt

	echo "Done."
}

main
