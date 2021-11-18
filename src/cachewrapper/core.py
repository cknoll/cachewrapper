import inspect
import json

# useful for debugging during development
try:
    from ipydex import IPS, activate_ips_on_exception
    activate_ips_on_exception()
except ImportError:
    pass


class CacheWrapper:
    """
    Wrapper object
    """

    def __init__(self, obj) -> None:
        """
        Create a wrapper
        """

        self.cache = {}

        self.wrapped_object = obj
        self.callables = get_all_callables(obj)
        self._create_wrapped_callables()

    def _create_wrapped_callables(self):
        for name, obj in self.callables.items():
            self._cached_func_factory(name, obj)

    def _cached_func_factory(self, name, obj):
        """
        Create a new callable obj and install it in the namespace of `self`.
        """

        def func(*args, **kwargs):

            # caching assumes that the arguments can be sensibly converted to json
            cache_key = (name, json.dumps(args, sort_keys=True), json.dumps(kwargs, sort_keys=True))
            try:
                return self.cache[cache_key]
            except KeyError:
                res = obj(*args, **kwargs)  # make the call
                self.cache[cache_key] = res  # store result in the cache
                return res

        func.__doc__ = f"{obj}wrapped callable '{name}':\n\n {obj.__doc__}"
        assert getattr(self, name, None) is None
        setattr(self, name, func)


def get_all_callables(obj, include_private=None) -> dict:

    if include_private is None:
        include_private = []
    attribute_names = dir(obj)
    attribute_dict = dict((name, getattr(obj, name)) for name in attribute_names)

    callables = dict(
        (name, obj)
        for (name, obj) in attribute_dict.items()
        if callable(obj) and (not name.startswith("_") or name in include_private)
    )

    return callables
