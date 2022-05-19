[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Python application](https://github.com/cknoll/cachewrapper/actions/workflows/python-app.yml/badge.svg)](https://github.com/cknoll/cachewrapper/actions/workflows/python-app.yml)

# Cachewrapper

**Use case**: you have modules or objects whose methods you want to call. These calls might be expensive (e.g. rate-limited API calls). Thus you do not want to make unnecessary calls which would only give results that you already have. However, during testing repeatedly calling these methods is unavoidable. *Cachewrapper* solves this by automatically providing a cache for all calls.


Currently this package is an early prototype, mainly for personal use.

## Installation


- clone the repository
- run `pip install -e .` (run from where `setup.py` lives).


## Usage Example


This is extracted from a real usecase (and not directly runable due to abridgement).

```

import os
from tqdm import tqdm
import cachewrapper as cw

# rate limited API module
from translate import Translator

cache_path = "translate_cache.pcl"
cached_translator = cw.CacheWrapper(original_translator)

if os.path.isfile(cache_path):
    cached_translator.load_cache(cache_path)

# not shown in this example
untranslated_classes = do_some_ontology_stuff()

res_list = []

for c in tqdm(untranslated_classes[:]):
    original = c.label.ru[0]
    translation = cached_translator.translate(original)

    if "MYMEMORY WARNING: YOU USED ALL AVAILABLE FREE TRANSLATIONS FOR TODAY" in translation:
        cached_translator._remove_last_key()
        break

    record = {
        c.name: {
            "ru": f"{original}",
            "en": f"{translation}",
        }
     }

    res_list.append(record)

cached_translator.save_cache(cache_path)

```
