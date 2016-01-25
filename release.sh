#!/usr/bin/env bash
# TODO delete this file and make Travis release the package on tag

# print what it's doing and exit on failed command
set -ex

# run the tests
tox

# clean up
rm -rf build dist

# get the latest json data
./updatejson.py

# build the release source dist and wheel
python setup.py sdist bdist_wheel

# stop printing what it's doing
set +x

cat << EOF

The built packages are now in './dist'. Test them and then
upload them to PyPI with the following command:

    $ twine upload -s dist/*

See this post for details:

    https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/
EOF
