[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Python application](https://github.com/cknoll/cachewrapper/actions/workflows/python-app.yml/badge.svg)](https://github.com/cknoll/cachewrapper/actions/workflows/python-app.yml)

# Cachewrapper

**Use case**: you have modules or objects whose methods you want to call. These calls might be expensive (e.g. rate-limited API calls). Thus you do not want to make unnecessary calls which would only give results that you already have. However, during testing repeatedly calling these methods is unavoidable. *Cachewrapper* solves this by automatically providing a cache for all calls.


Currently this package is an early prototype, mainly for personal use.

## Installation


- clone the repository
- run `pip install -e .` (run from where `setup.py` lives).


## Usage Example


This is extracted from a real use case (translating a math ontology which originally contained mainly Russian labels)
and not directly executable due to abridgement.

```python
import os
from tqdm import tqdm
import cachewrapper as cw


# suppose data contains strings which should be translated into english
from . import data

# rate limited API module
from translate import Translator

cache_path = "translate_cache.pcl"
cached_translator = cw.CacheWrapper(Translator)

if os.path.isfile(cache_path):
    cached_translator.load_cache(cache_path)

res_list = []

for original_label in tqdm(data.untranslated_labels):
    translation = cached_translator.translate(original_label)

    if "MYMEMORY WARNING: YOU USED ALL AVAILABLE FREE TRANSLATIONS FOR TODAY" in translation:
        # we ran into the rate-limit -> we do not want to save this result
        cached_translator._remove_last_key()
        break

    record = {
        "ru": f"{original_label}",
        "en": f"{translation}",
     }

    res_list.append(record)

cached_translator.save_cache(cache_path)

```


There are more features implemented but not yet properly documented:

- unpacking of returned iterators (up to a maximum size)
- `_last_cache_status` to check if the last call could retrieve a result from the cache
    - helpful to decide whether to call `time.sleep(3)` to prevent rate limiting
