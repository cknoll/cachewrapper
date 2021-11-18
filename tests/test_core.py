import unittest
import cachewrapper as cw

# useful for debugging during development
try:
    from ipydex import IPS, activate_ips_on_exception

    activate_ips_on_exception()
except ImportError:
    pass


class DummyClass:
    def __init__(self) -> None:
        self.call_counter = 0

    def _private_method(self):
        """
        docstring of _private_method
        """
        self.call_counter += 1

    def public_method1(self, arg1, arg2):
        """
        docstring of public_method1
        """
        self.call_counter += 1

        if isinstance(arg1, dict) and isinstance(arg2, dict):
            return dict(**arg1, **arg2)

        return arg1 + arg2

    def public_method2(self, arg1, arg2):
        """
        docstring of public_method2
        """
        self.call_counter += 1
        return arg1 + arg2

    def public_method3(self, *args):
        """
        docstring of public_method3: only return self
        """
        self.call_counter += 1
        return self

    def staticmethod1(self, arg1, arg2):
        """
        docstring of staticmethod1
        """
        self.call_counter += 1
        return arg1 + arg2


# noinspection PyPep8Naming
class TestCore(unittest.TestCase):
    def setUp(self):
        pass

    def test_CW_get_all_functions_and_methods(self):

        instance = DummyClass()
        cached_instance = cw.CacheWrapper(instance)

        self.assertEqual(len(cached_instance.callables), 4)

    def test_caching(self):

        original_instance = DummyClass()
        cached_instance = cw.CacheWrapper(original_instance)

        original_callables = cw.get_all_callables(original_instance)
        new_callables = cw.get_all_callables(cached_instance)

        self.assertEqual(len(original_callables), len(new_callables))

        self.assertIn("docstring of public_method1", cached_instance.public_method1.__doc__)

        self.assertEqual(original_instance.call_counter, 0)
        self.assertEqual(len(cached_instance.cache), 0)

        res1 = original_instance.public_method3()
        self.assertEqual(original_instance.call_counter, 1)
        res2 = cached_instance.public_method3()
        self.assertEqual(original_instance.call_counter, 2)
        self.assertEqual(len(cached_instance.cache), 1)
        res3 = cached_instance.public_method3()
        self.assertEqual(len(cached_instance.cache), 1)
        self.assertEqual(original_instance.call_counter, 2)
        self.assertEqual(res1, res2)
        self.assertEqual(res1, res3)

        # public_method1

        cc = original_instance.call_counter
        res1 = original_instance.public_method1(10, 5)  # -> raw call
        self.assertEqual(original_instance.call_counter, cc + 1)  # new call
        res2 = cached_instance.public_method1(10, 5)  # -> results in raw call
        self.assertEqual(original_instance.call_counter, cc + 2)  # new call
        self.assertEqual(len(cached_instance.cache), 2)  # increased cache
        res3 = cached_instance.public_method1(10, 5)  # -> cached call
        self.assertEqual(original_instance.call_counter, cc + 2)
        self.assertEqual(len(cached_instance.cache), 2)

        self.assertEqual(res1, res2)
        self.assertEqual(res2, res3)

        # public_method1 with dicts as args

        arg1 = {"a": 1}
        arg2 = {"b": 2}

        cc = original_instance.call_counter

        res1 = original_instance.public_method1(arg1, arg2)  # -> raw call
        self.assertEqual(original_instance.call_counter, cc + 1)  # new call
        res2 = cached_instance.public_method1(arg1, arg2)  # -> results in raw call
        self.assertEqual(original_instance.call_counter, cc + 2)  # new call
        self.assertEqual(len(cached_instance.cache), 3)  # increased cache
        res3 = cached_instance.public_method1(arg1, arg2)  # -> cached call
        self.assertEqual(original_instance.call_counter, cc + 2)  # no new call
        self.assertEqual(len(cached_instance.cache), 3)  # no new cache entry

        self.assertEqual(res1, res2)
        self.assertEqual(res2, res3)
