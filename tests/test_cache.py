import unittest

from lambdex.keywords import def_
from lambdex.compiler import cache, core


class TestCacheEnableDisable(unittest.TestCase):
    def setUp(self):
        core.__DEBUG__ = True

    def tearDown(self):
        cache.set_enabled(True)
        core.__DEBUG__ = False

    def test_code_and_ast_is_same_when_cache_enabled(self):
        def f():
            return def_(lambda: [
                return_[1 + 1],
            ])

        cache.set_enabled(True)
        f1 = f()
        f2 = f()
        self.assertEqual(f1.__code__.co_name, f2.__code__.co_name)
        self.assertIs(f1.__ast__, f2.__ast__)

    def test_code_and_ast_is_different_when_cache_disabled(self):
        def f():
            return def_(lambda: [
                return_[1 + 1],
            ])

        cache.set_enabled(False)
        f1 = f()
        f2 = f()
        self.assertNotEqual(f1.__code__.co_name, f2.__code__.co_name)
        self.assertIsNot(f1.__ast__, f2.__ast__)


class TestEdgeCase(unittest.TestCase):
    def setUp(self):
        core.__DEBUG__ = True

    def tearDown(self):
        core.__DEBUG__ = False

    def test_lambdex_on_the_same_line_should_be_different(self):
        def f():
            return def_.a(lambda: [
                return_[1 + 1],
            ]), def_(lambda: [
                return_[1 + 2],
            ])

        f1, f2 = f()
        self.assertNotEqual(f1.__code__.co_name, f2.__code__.co_name)
        self.assertIsNot(f1.__ast__, f2.__ast__)
