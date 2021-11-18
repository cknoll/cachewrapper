#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import setuptools
from setuptools import setup, find_packages


packagename = "cachewrapper"

# consider the path of `setup.py` as root directory:
PROJECTROOT = os.path.dirname(sys.argv[0]) or "."
release_path = os.path.join(PROJECTROOT, "src", packagename, "release.py")
with open(release_path, encoding="utf8") as release_file:
    __version__ = release_file.read().split('__version__ = "', 1)[1].split('"', 1)[0]


with open("requirements.txt") as requirements_file:
    requirements = requirements_file.read()

setup(
    name=packagename,
    version=__version__,
    author="Carsten Knoll",
    author_email="firstname.lastname@posteo.de",
    packages=find_packages("src"),
    package_dir={"": "src"},
    url="https://codeberg.org/cark/cachewrapper",
    license="GPLv3",
    description="thin layer to facilitate caching of api calls",
    long_description="""
    **Use case**: you have modules or objects whose methods you want to call. These calls might be expensive (e.g. rate-limited API calls). Thus you do not want to make unnecessary calls which would only give results that you already have. However, during testing repeatedly calling these methods is unavoidable. *Cachewrapper* solves this by automatically providing a cache for all calls.
    """,
    install_requires=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
    ],
)
