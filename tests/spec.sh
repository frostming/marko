#!/usr/bin/env bash

set -e

REPO="https://github.com/commonmark/CommonMark.git"
VERSION=$1

if [ -z "$VERSION" ]; then
	echo 'Please give spec version to dump: ./spec.sh $VERSION'
	exit 1
fi

function main {
	echo "Downloading spec file $VERSION..."
	curl "https://raw.githubusercontent.com/commonmark/commonmark-spec/$VERSION/spec.txt" -o spec.txt
	# No corresponding tag on GFM spec, use master anyway
	curl "https://raw.githubusercontent.com/github/cmark-gfm/master/test/spec.txt" -o gfm.txt

	echo "Dumping tests file..."
	python3 -m spec --dump spec.txt > spec/commonmark.json
	python3 -m spec --dump gfm.txt > spec/gfm.json

	echo "Cleaning up..."
	rm -rf spec.txt
	rm -fr gfm.txt

	echo "Done."
}

main
