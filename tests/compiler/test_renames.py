import unittest

from lambdex import def_


class TestRename(unittest.TestCase):
    def test_outer_rename(self):
        f = def_.myfunc(lambda: [
            pass_
        ])

        self.assertEqual(f.__code__.co_name, "myfunc")

    def test_inner_rename(self):
        f = def_.myfunc(lambda: [
            return_[def_.myfunc_inner(lambda: [
                pass_
            ])]
        ])

        self.assertEqual(f().__code__.co_name, "myfunc_inner")

    def test_inner_rename_not_expose(self):
        f = def_.myfunc(lambda: [
            a < def_.myfunc_inner(lambda: [
                pass_
            ]),
            myfunc_inner,
        ])

        with self.assertRaises(NameError) as cm:
            f()
