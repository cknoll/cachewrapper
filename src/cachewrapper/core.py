import inspect
from ipydex import IPS, activate_ips_on_exception

activate_ips_on_exception()


class CacheWrapper:
    """
    Wrapper object
    """

    def __init__(self, obj) -> None:
        """
        Create a wrapper
        """

        self.wrapped_object = obj
        self.callables = get_all_callables(obj)
        self._create_wrapped_callables()

    def _create_wrapped_callables(self):
        for name, obj in self.callables.items():
            self._cached_func_factory(name, obj)

    def _cached_func_factory(self, name, obj):
        """
        create a new callable obj and install it in the namespace of `self`
        """

        def func(*args, **kwargs):
            return obj(*args, **kwargs)

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
