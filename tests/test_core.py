import unittest
import cachewrapper as cw
import os

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

    def public_method2(self, arg1):
        """
        docstring of public_method2: return an iterator
        """
        self.call_counter += 1
        res = iter(range(arg1))
        return res

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


    def test_20_caching_of_ordinary_function(self):

        func1_call_counter = 0
        def func1(arg1, arg2):
            """
            This is the original docstring
            """
            nonlocal func1_call_counter
            func1_call_counter += 1
            return func1_call_counter

        cached_func1 = cw.CacheWrapper(func1)

        self.assertIsNone(cached_func1._last_cache_status)

        cached_func1(10, 20)
        self.assertEqual(func1_call_counter, 1)
        self.assertFalse(cached_func1._last_cache_status)
        cached_func1(10, 20)
        self.assertEqual(func1_call_counter, 1)
        self.assertTrue(cached_func1._last_cache_status)

        cached_func1(0, 20)
        self.assertEqual(func1_call_counter, 2)
        self.assertFalse(cached_func1._last_cache_status)


        self.assertIn(func1.__doc__, cached_func1.__doc__)


    def test_caching1(self):

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
        self.assertEqual(cached_instance.cache.read_counter, 0)
        res3 = cached_instance.public_method3()
        self.assertEqual(len(cached_instance.cache), 1)
        self.assertEqual(cached_instance.cache.read_counter, 1)
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
        self.assertEqual(cached_instance.cache.read_counter, 1)
        res3 = cached_instance.public_method1(10, 5)  # -> cached call
        self.assertEqual(original_instance.call_counter, cc + 2)
        self.assertEqual(cached_instance.cache.read_counter, 2)
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
        self.assertEqual(
            cached_instance.cache.read_counter, 2
        )  # no new successful read access to the cache
        res3 = cached_instance.public_method1(arg1, arg2)  # -> cached call
        self.assertEqual(original_instance.call_counter, cc + 2)  # no new call
        self.assertEqual(
            cached_instance.cache.read_counter, 3
        )  # new successful read access to the cache
        self.assertEqual(len(cached_instance.cache), 3)  # no new cache entry

        self.assertEqual(res1, res2)
        self.assertEqual(res2, res3)

    def test_pop_last_key(self):

        ##!!

        original_instance = DummyClass()
        cached_instance = cw.CacheWrapper(original_instance)

        self.assertEqual(len(cached_instance.cache), 0)

        res1 = cached_instance.public_method1(10, 5)  # -> new call

        self.assertEqual(len(cached_instance.cache), 1)

        res1 = cached_instance.public_method1(10, 5)  # -> new call
        res1 = cached_instance.public_method1(10, 5)  # -> new call
        self.assertEqual(original_instance.call_counter, 1)

        res2 = cached_instance._remove_last_key()
        self.assertEqual(res1, res2)
        self.assertEqual(len(cached_instance.cache), 0)

        res3 = cached_instance.public_method1(10, 5)  # -> new call
        self.assertEqual(original_instance.call_counter, 2)

    def test_caching_with_save_and_load(self):

        original_instance = DummyClass()
        cached_instance = cw.CacheWrapper(original_instance)

        cache_path = "cache.pcl"

        arg1 = {"a": 1, "x": {1: []}}
        arg2 = {"b": 2}

        cc = original_instance.call_counter

        res1 = original_instance.public_method1(arg1, arg2)  # -> raw call
        res2 = cached_instance.public_method1(arg1, arg2)  # -> results in raw call again

        self.assertEqual(original_instance.call_counter, 2)

        cached_instance.save_cache(cache_path)
        cached_instance.cache.clear()

        res3 = cached_instance.public_method1(
            arg1, arg2
        )  # -> again in raw call (due to empty cache)
        self.assertEqual(original_instance.call_counter, 3)
        cached_instance.cache.clear()

        cached_instance.load_cache(cache_path)
        res4 = cached_instance.public_method1(arg1, arg2)  # -> no new call
        self.assertEqual(original_instance.call_counter, 3)

        self.assertEqual(res1, res2)
        self.assertEqual(res1, res3)
        self.assertEqual(res1, res4)

        os.remove(cache_path)

    def test_caching_iterators(self):
        original_instance = DummyClass()
        cached_instance = cw.CacheWrapper(original_instance)

        res1 = cached_instance.public_method2(8)
        self.assertEqual(list(res1), list(range(5)))  # default length for unpacked iterators = 5
        self.assertEqual(cached_instance.cache.read_counter, 0)

        with self.assertRaises(ValueError) as cm:
            # this call should trigger an exception because the requested iterator length is not
            # present in the cache
            res1 = cached_instance.public_method2(8, cw_unpacked_iterator_limit=20)

        # the previous call nevertheless counts as read access to the cache
        self.assertEqual(cached_instance.cache.read_counter, 1)

        # this is OK, since the cache is explicitly deactivated
        res1 = cached_instance.public_method2(
            8, cw_unpacked_iterator_limit=20, cw_override_cache=True
        )
        self.assertEqual(list(res1), list(range(8)))  # default of 5 length now overridden
        self.assertEqual(cached_instance.cache.read_counter, 1)

        res1 = cached_instance.public_method2(8)
        self.assertEqual(cached_instance.cache.read_counter, 2)
        self.assertEqual(list(res1), list(range(8)))  # default length of 5 still overridden

        cached_instance2 = cw.CacheWrapper(original_instance, cw_unpacked_iterator_limit=30)

        res1 = cached_instance2.public_method2(25)
        self.assertEqual(list(res1), list(range(25)))  # default length sufficiently large
        self.assertEqual(cached_instance2.cache.read_counter, 0)

        res1 = cached_instance2.public_method2(25)
        self.assertEqual(list(res1), list(range(25)))  # default length sufficiently large
        self.assertEqual(cached_instance2.cache.read_counter, 1)

    def test_caching_multiple_objects1(self):
        class DummyClass2:
            def __init__(self) -> None:
                self.call_counter = 0

            def dc2_public_method1(self, arg1, arg2):
                """
                docstring of public_method1
                """
                self.call_counter += 1

        original_instance1 = DummyClass()
        cached_instance1 = cw.CacheWrapper(original_instance1)

        original_instance2 = DummyClass2()
        cached_instance2 = cw.CacheWrapper(original_instance2, share_cache_with=cached_instance1)

        self.assertEqual(len(cached_instance1.cache), 0)
        self.assertEqual(len(cached_instance2.cache), 0)

        cached_instance1.public_method1(1, 2)
        self.assertEqual(len(cached_instance1.cache), 1)
        self.assertEqual(len(cached_instance2.cache), 1)

        cached_instance2.dc2_public_method1(1, 2)
        self.assertEqual(len(cached_instance1.cache), 2)
        self.assertEqual(len(cached_instance2.cache), 2)

        cached_instance2.dc2_public_method1(1, 2)
        self.assertEqual(len(cached_instance1.cache), 2)
        self.assertEqual(len(cached_instance2.cache), 2)

        original_instance3 = DummyClass2()

        with self.assertRaises(ValueError) as cm:
            # this call should trigger an exception because there are duplicated names
            cached_instance3 = cw.CacheWrapper(
                original_instance3, share_cache_with=cached_instance1
            )
