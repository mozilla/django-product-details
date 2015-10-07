#!/usr/bin/env bash

# print what it's doing and exit on failed command
set -ex

# run the tests
tox

# get the latest json data
./updatejson.py

# release to pypi
python setup.py sdist upload
