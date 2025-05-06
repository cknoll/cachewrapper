import inspect
import json
import pickle
import collections

# useful for debugging during development
try:
    from ipydex import IPS, activate_ips_on_exception  # noqa

    activate_ips_on_exception()
except ImportError:
    pass


class CountingDict(dict):
    """
    Dict that counts how often a successful read-access has occurred
    """

    def __init__(self, *args, **kwargs):
        self.read_counter = 0
        return super().__init__(*args, **kwargs)

    def __getitem__(self, __k):
        res = super().__getitem__(__k)
        self.read_counter += 1
        return res

    def get(self, *args, **kwargs):
        res = super().get(*args, **kwargs)
        self.read_counter += 1
        return res


class CacheWrapper:
    """
    Wrapper object
    """

    def __init__(
        self, obj, cw_unpacked_iterator_limit=5, share_cache_with: "CacheWrapper" = None
    ) -> None:
        """
        Create a wrapper
        :param cw_unpacked_iterator_limit:  default value for how many items of an iterator
                                            are unpacked in the cached result.
        """

        if share_cache_with is None:
            self.cache = CountingDict()
            self.cache_sharing_objects = set([self])
        else:
            assert isinstance(share_cache_with, CacheWrapper), f"Unexpected Type:{type(share_cache_with)}"
            self.cache = share_cache_with.cache
            self.cache_sharing_objects = set([self]).union(share_cache_with.cache_sharing_objects)
            share_cache_with.cache_sharing_objects.add(self)

        self.cw_unpacked_iterator_limit = cw_unpacked_iterator_limit

        self.wrapped_object = obj
        self.callables = get_all_callables(obj)
        self._prevent_name_clashes()
        self._create_wrapped_callables()
        self._last_used_key = None

        # True if the last call was a cached call, False if not
        self._last_cache_status = None

        # initialize with True to allow saving even with no result
        self._cache_contains_unsaved_data = True

        if callable(obj):
            self.__doc__ = f"Wrapped callable object:\n\n {obj.__doc__}"

    def __call__(self, *args, **kwargs):

        call_func = getattr(self, "_real_call__", None)
        if call_func is None:
            msg = f"{self} is not callable because the wrapped object was not callable."
            raise TypeError(msg)

        return call_func(*args, **kwargs)

    def _remove_last_key(self):
        """
        Removes the last used key from the cache. This is useful if the call retrieved an error
        (e.g. rate-limit) instead of the desired result.

        :return:    cached result
        """

        assert self._last_used_key is not None
        res = self.cache.pop(self._last_used_key)

        return res

    def _prevent_name_clashes(self):
        my_callables = set(self.callables.keys())

        other_callables = set()
        for other_obj in self.cache_sharing_objects:
            if other_obj is self:
                continue
            else:
                other_callables.update(other_obj.callables.keys())

        duplicate_names = my_callables.intersection(other_callables)
        if len(duplicate_names) > 0:
            msg = f"There are the following duplicate names:\n{duplicate_names}"
            raise ValueError(msg)

    def _create_wrapped_callables(self):
        for name, obj in self.callables.items():
            self._cached_func_factory(name, obj)

    def _cached_func_factory(self, name, obj):
        """
        Create a new callable obj and install it in the namespace of `self`.
        """

        # note: `name` and `obj` are specific to the following function-object
        def func(*args, **kwargs):

            # pop some args which should not be passed to the original function

            cw_unpacked_iterator_limit = kwargs.pop(
                "cw_unpacked_iterator_limit", self.cw_unpacked_iterator_limit
            )
            cw_override_cache = kwargs.pop("cw_override_cache", False)

            # caching requires that arguments can be hashed -> convert the to str
            cache_key = (name, args_to_key(args), args_to_key(kwargs))

            # ## Saving to the cache:
            #
            # iterators need some special handling because they are "empty" after reading
            # thus it would be pointless to cache an iterator directly
            # instead it is unpacked and stored as (wrapped) list.
            # However to have the same output as the original function we have to return
            # a new iterator.
            #
            #
            # ## Reading from the cache:
            #
            # An IteratorWrapper has to be converted back to an iterator

            try:
                if cw_override_cache:
                    # act as if the value was not in the cache
                    raise KeyError

                # try to get the cached result
                res = self.cache[cache_key]

                # handle special case of Iterators
                if isinstance(res, IteratorWrapper):
                    if cw_unpacked_iterator_limit > res.max_size:
                        msg = (
                            f"The cached IteratorWrapper only has max_size of {res.max_size}.\n"
                            f"You want a length of {cw_unpacked_iterator_limit}.\n"
                            "You might want to use `cw_override_cache=True`."
                        )
                        raise ValueError(msg)
                    res = res.get_iter()

                self._last_cache_status = True
                return res
            except KeyError:
                res = obj(*args, **kwargs)  # make the call to the original callable object
                self._cache_contains_unsaved_data = True

                if isinstance(res, collections.abc.Iterator):
                    cache_res = IteratorWrapper(res, max_size=cw_unpacked_iterator_limit)
                    res = cache_res.get_iter()
                else:
                    cache_res = res

                self.cache[cache_key] = cache_res  # store the (wrapped) result in the cache
                self._last_used_key = cache_key
                self._last_cache_status = False
                return res

        # generate a new docstring from the old one
        func.__doc__ = f"wrapped callable '{name}':\n\n {obj.__doc__}"
        assert getattr(self, name, None) is None
        setattr(self, name, func)

    def save_cache(self, path: str, only_if_changed: bool = False):

        if only_if_changed and (not self._cache_contains_unsaved_data):
            # we do not need to save the cache again
            return
        with open(path, "wb") as fp:
            pickle.dump(self.cache, fp)

        # we just saved the cache -> obviously no unsaved data left
        self._cache_contains_unsaved_data = False

    def load_cache(self, path: str):
        with open(path, "rb") as fp:
            pdict = pickle.load(fp)
        self.cache.update(pdict)

        self._cache_contains_unsaved_data = False


def args_to_key(obj):
    """
    Convert any object which can be passed to a cached function to a string representation
    (to identify its reoccurrence)
    """

    try:
        # this is preferred but does not always work
        res = json.dumps(obj, sort_keys=True)
    except TypeError:
        # this might be ambiguous
        res = str(obj)

    return res


class IteratorWrapper:
    def __init__(self, iter_obj: collections.abc.Iterator, max_size):

        self.max_size = max_size
        self.unpacked_sequence = []
        for i, item in enumerate(iter_obj):
            if i >= max_size:
                break
            self.unpacked_sequence.append(item)

    def get_iter(self):
        return iter(self.unpacked_sequence)


def get_all_callables(
    obj, include_private=None, exclude_names=("save_cache", "load_cache")
) -> dict:

    if include_private is None:
        include_private = []
    attribute_names = dir(obj)
    attribute_dict = dict((name, getattr(obj, name)) for name in attribute_names)

    callables = dict(
        (name, obj)
        for (name, obj) in attribute_dict.items()
        if callable(obj)
        and (not name.startswith("_") or name in include_private)
        and name not in exclude_names
    )

    if callable(obj):
        if isinstance(obj, CacheWrapper):
            if callable(obj.wrapped_object):
                # all CacheWrapper-objects have a __call__ method
                # however, we only consider those as callable for which the original object was also callable
                # (the other case  deliberately results in a TypeError anyway)
                cond = True
            else:
                cond = False
        else:
            cond = True

        if cond:
            callables.update(_real_call__=obj)

    return callables
