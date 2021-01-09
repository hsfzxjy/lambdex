import unittest

from lambdex.keywords import def_

VAR = 1


class TestScoping(unittest.TestCase):
    def setUp(self):
        global VAR
        VAR = 1

    def test_load_global_without_keyword(self):
        f = def_(lambda: [
            return_[VAR],
        ])

        self.assertEqual(f(), 1)

    def test_load_global_with_keyword(self):
        f = def_(lambda: [
            global_[VAR],
            return_[VAR],
        ])

        self.assertEqual(f(), 1)

    def test_set_global(self):
        f = def_(lambda: [
            global_[VAR],
            VAR <= 2,
            return_[VAR],
        ])

        self.assertEqual(f(), 2)
        self.assertEqual(VAR, 2)

    def test_set_global_fail_of_no_global_keyword(self):
        f = def_(lambda: [
            VAR <= 2,
            return_[VAR],
        ])

        self.assertEqual(f(), 2)
        self.assertEqual(VAR, 1)

    def test_load_nonlocal_without_keyword(self):
        VAR = 2
        f = def_(lambda: [
            return_[VAR],
        ])

        self.assertEqual(f(), 2)

    def test_load_nonlocal_with_keyword(self):
        VAR = 2
        f = def_(lambda: [
            nonlocal_[VAR],
            return_[VAR],
        ])

        self.assertEqual(f(), 2)

    def test_set_nonlocal(self):
        VAR = 2
        f = def_(lambda: [
            nonlocal_[VAR],
            VAR <= VAR + 2,
            return_[VAR],
        ])

        def _assert_global_VAR_is(x):
            global VAR
            self.assertEqual(VAR, x)

        self.assertEqual(f(), 4)
        self.assertEqual(VAR, 4)
        _assert_global_VAR_is(1)

    def test_set_nonlocal_fail_of_no_nonlocal_keyword(self):
        VAR = 2
        f = def_(lambda: [
            VAR <= 4,
            return_[VAR],
        ])

        self.assertEqual(f(), 4)
        self.assertEqual(VAR, 2)

    def test_set_global_while_same_name_variable_exists_in_parent_scope(self):
        VAR = 2
        f = def_(lambda: [
            global_[VAR],
            VAR <= 4,
            return_[VAR],
        ])

        def _assert_global_VAR_is(x):
            global VAR
            self.assertEqual(VAR, x)

        self.assertEqual(f(), 4)
        self.assertEqual(VAR, 2)
        _assert_global_VAR_is(4)


class TestNested(unittest.TestCase):
    def test_load_nonlocal(self):
        f = def_(lambda VAR: [
            return_[def_(lambda: [  #
                return_[VAR],
            ])]
        ])

        self.assertEqual(f(4)(), 4)
        self.assertEqual(VAR, 1)

    def test_IIFE(self):
        import lambdex.compiler.core as core
        from lambdex.utils.ast import pprint
        core.__DEBUG__ = True
        f = def_(
            lambda: [
                ret <= [],  #
                for_[i in range(10)][  #
                    def_(lambda i: [  #
                        ret.append(  #
                            def_(lambda: [  #
                                return_[i]  #
                            ])
                        )  #
                    ])(i)  #
                ],
                return_[ret],
            ]
        )

        ret = f()
        stored_variables = [x() for x in ret]
        self.assertEqual(stored_variables, list(range(10)))
