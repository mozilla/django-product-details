import codecs
import os.path
import re

from setuptools import find_packages, setup


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
    author="Fred Wenzel",
    author_email="fwenzel@mozilla.com",
    url="https://github.com/mozilla/django-product-details/",
    license="BSD",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["Django>=2.2", "requests>=2.21.0"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Environment :: Web Environment :: Mozilla",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
