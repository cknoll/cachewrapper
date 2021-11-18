import unittest
import cachewrapper as cw

from ipydex import IPS, activate_ips_on_exception


class DummyClass:
    def __init__(self) -> None:
        pass

    def _private_method(self):
        """
        docstring of _private_method
        """

    def public_method1(self, arg1, arg2):
        """
        docstring of public_method1
        """
        return arg1 + arg2

    def public_method2(self, arg1, arg2):
        """
        docstring of public_method2
        """
        return arg1 + arg2

    def public_method3(self, *args):
        """
        docstring of public_method3: only return self
        """
        return self

    def staticmethod1(self, arg1, arg2):
        """
        docstring of staticmethod1
        """
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

        res1 = original_instance.public_method3()
        res2 = cached_instance.public_method3()

        self.assertEqual(res1, res2)
