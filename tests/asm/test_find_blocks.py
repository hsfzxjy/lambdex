import io
import dis
import unittest
from lambdex.compiler.asm.core import _find_lambdex_blocks


class TestFindBlocks(unittest.TestCase):
    def assert_has_n_lambdex(self, f, n):
        blocks = list(_find_lambdex_blocks(f.__code__))

        ostream = io.StringIO()
        dis.dis(f, file=ostream)
        self.assertEqual(len(blocks), n, 'DISASSEMBLY:\n' + ostream.getvalue())

    def test_normal(self):
        def f():
            def_(lambda: [
                pass_
            ])

        self.assert_has_n_lambdex(f, 1)

    def test_nested(self):
        def f():
            def_(lambda: [
                def_(lambda: [
                    pass_
                ])
            ])

        self.assert_has_n_lambdex(f, 1)

    def test_arg_default_attribute(self):
        def f():
            def_(lambda a=a.b: [
                pass_
            ])

        self.assert_has_n_lambdex(f, 1)

    def test_arg_default_constant(self):
        def f():
            def_(lambda a=1: [
                pass_
            ])

        self.assert_has_n_lambdex(f, 1)

    def test_arg_default_ifelse_folded(self):
        def f():
            def_(lambda a=1 if 1 + 1 else 2: [
                pass_
            ])

        self.assert_has_n_lambdex(f, 1)

    def test_arg_default_ifelse_unfolded(self):
        def f():
            def_(lambda a=1 if 1 + 1 > 2 else 2: [
                pass_
            ])

        self.assert_has_n_lambdex(f, 1)

    def test_arg_default_logic_folded(self):
        def f():
            def_(lambda a=1 or 2, b=1 and 2, c=1 or 2 and 3: [
                pass_
            ])

        self.assert_has_n_lambdex(f, 1)

    def test_arg_default_logic_unfolded(self):
        def f():
            def_(lambda a=1 + 1 > 2 or 2, b=1 + 1 > 2 and 2, c=a or b or c: [
                pass_
            ])

        self.assert_has_n_lambdex(f, 1)

    def test_arg_default_lambda(self):
        def f():
            def_(lambda a=lambda: 1: [
                pass_
            ])

        self.assert_has_n_lambdex(f, 1)

    def test_arg_default_lambda_call(self):
        def f():
            def_(lambda a=a(lambda: 1)(): [
                pass_
            ])

        self.assert_has_n_lambdex(f, 1)

    def test_arg_default_lambdex(self):
        def f():
            def_(lambda a=def_(lambda: [
                pass_
            ]): [
                pass_
            ])

        self.assert_has_n_lambdex(f, 2)

    def test_arg_default_lambdex_x2(self):
        def f():
            def_(lambda a=def_(lambda: [
                pass_
            ]), b=def_(lambda: [
                pass_
            ]): [
                pass_
            ])

        self.assert_has_n_lambdex(f, 3)

    def test_arg_default_lambdex_arg_default_lambdex(self):
        def f():
            def_(lambda a=def_(lambda a=def_(lambda: [
                pass_
            ]): [
                pass_
            ]): [
                pass_
            ])

        self.assert_has_n_lambdex(f, 3)

    def test_complex(self):
        def f():
            def_(lambda a=def_(lambda a=def_(lambda: [
                pass_
            ]), b=def_(lambda: [
                pass_
            ]), c=a if b else c or d and e or f: [
                pass_
            ]): [
                pass_
            ])

        self.assert_has_n_lambdex(f, 4)
