import codecs
import os.path
import re

from setuptools import find_namespace_packages, setup


def find_version(*file_paths):
    version_file = codecs.open(
        os.path.join(os.path.dirname(__file__), *file_paths), "rb", encoding="utf8"
    ).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="django-mozilla-product-details",
    version=find_version("product_details", "__init__.py"),
    description="Product and locale details for Mozilla products.",
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    author="Fred Wenzel",
    author_email="fwenzel@mozilla.com",
    url="https://github.com/mozilla/django-product-details/",
    license_expression="BSD-3-Clause",
    # find_namespace_packages so that the product_details/json data directories
    # (which have no __init__.py) are treated as packages and shipped.
    packages=find_namespace_packages(include=["product_details", "product_details.*"]),
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10",
    install_requires=["Django>=4.2", "requests>=2.26.0"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Environment :: Web Environment :: Mozilla",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
