[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Cachewrapper

**Use case**: you have modules or objects whose methods you want to call. These calls might be expensive (e.g. rate-limited API calls). Thus you do not want to make unnecessary calls which would only give results that you already have. However, during testing repeatedly calling these methods is unavoidable. *Cachewrapper* solves this by automatically providing a cache for all calls.


Currently this package is an early prototype, mainly for personal use.

## Installation


- clone the repository
- run `pip install -e .` (run from where `setup.py` lives).

