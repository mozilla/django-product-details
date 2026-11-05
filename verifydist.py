#!/usr/bin/env python
"""
Check that the built distributions in dist/ actually contain the
product-details JSON data.

The JSON files are not committed to git; they are fetched by
``updatejson.py`` right before ``python -m build``. If that step is skipped
or fails quietly, we would publish a package without any data (as happened
with 1.0.1 and 1.0.2), so the release workflow runs this before uploading.
"""
import glob
import sys
import tarfile
import zipfile

JSON_PREFIX = "product_details/json/"

# Files that must be present in every release.
REQUIRED_FILES = (
    "firefox_versions.json",
    "firefox_history_major_releases.json",
    "languages.json",
    "mobile_versions.json",
    "thunderbird_versions.json",
    "regions/en-US.json",
)

# Lower bound on the total number of JSON files. product-details currently
# ships ~130 (about 20 top-level files plus ~110 regions/*.json files).
MIN_JSON_FILES = 100


def json_members(names, strip_top_dir=False):
    """
    Return the JSON paths (relative to product_details/json/) in a member list.

    Only files at the package's real location count. Wheel members are
    relative to the archive root; sdist members live under a single
    "<name>-<version>/" directory, which is stripped first.
    """
    found = set()
    for name in names:
        if strip_top_dir:
            name = name.partition("/")[2]
        if name.startswith(JSON_PREFIX) and name.endswith(".json"):
            found.add(name[len(JSON_PREFIX):])
    return found


def check(path, names, strip_top_dir=False):
    found = json_members(names, strip_top_dir=strip_top_dir)
    problems = []
    if len(found) < MIN_JSON_FILES:
        problems.append(
            "only %d JSON files found, expected at least %d" % (len(found), MIN_JSON_FILES)
        )
    missing = [f for f in REQUIRED_FILES if f not in found]
    if missing:
        problems.append("missing required files: %s" % ", ".join(missing))

    if problems:
        print("FAIL %s: %s" % (path, "; ".join(problems)))
        return False

    print("OK   %s: %d JSON files, all required files present" % (path, len(found)))
    return True


def main(dist_dir="dist"):
    wheels = sorted(glob.glob("%s/*.whl" % dist_dir))
    sdists = sorted(glob.glob("%s/*.tar.gz" % dist_dir))
    if not wheels or not sdists:
        print("FAIL expected a wheel and an sdist in %s/, found: %s" % (dist_dir, wheels + sdists))
        return 1

    ok = True
    for whl in wheels:
        with zipfile.ZipFile(whl) as zf:
            ok &= check(whl, zf.namelist())
    for sdist in sdists:
        with tarfile.open(sdist) as tf:
            ok &= check(sdist, tf.getnames(), strip_top_dir=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
