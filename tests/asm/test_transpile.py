import sys
import dis
import unittest
import traceback
import linecache
from pathlib import Path
from textwrap import dedent
from lambdex.compiler.asm.core import transpile

from lambdex import def_


class TestTranspile(unittest.TestCase):
    def setUp(self):
        self.orig_getlines = linecache.getlines

        def _mock_getlines(filename, g=None):
            if filename == '<mod>':
                return self.lines
            return self.orig_getlines(filename, g)

        linecache.getlines = _mock_getlines

    def tearDown(self):
        linecache.getlines = self.orig_getlines

    def makecode(self, source: str):
        source = dedent(source).strip()
        self.lines = source.splitlines(keepends=True)

        code1 = compile(source, '<mod>', 'exec')
        code2 = transpile(code1, ismod=True)

        return code1, code2

    def test_case1(self):
        source = '''
        a = 1
        b = 2
        f = def_(lambda a=1 if 1 + 1 > 2 else 2, b=def_.a(lambda: [return_[callee_]]), c=a+b and b-a-a or a if a else b: [
            return_[a, b, c, callee_]
        ])
        '''

        code1, code2 = self.makecode(source)

        g = {'def_': def_}
        exec(code1, g)
        g = {}
        exec(code2, g)
        f = g['f']

        two, b, one, f_callee = f()
        self.assertEqual(one, 1)
        self.assertEqual(two, 2)
        self.assertIs(f, f_callee)
        self.assertEqual(b.__name__, 'a')
        self.assertIs(b, b())

    def test_case2(self):
        source = '''
        def func():
            return 1

        def gen_f():
            a = 1
            b = 2
            return def_(lambda a=1 if 1 + 1 > 2 else 2, b=def_.a(lambda: [return_[callee_]]), c=a+b and b-a-a or a if a else b: [
                return_[a, b, c, callee_]
            ])
        '''

        code1, code2 = self.makecode(source)

        g = {'def_': def_}
        exec(code1, g)
        g = {}
        exec(code2, g)
        gen_f = g['gen_f']
        func = g['func']

        self.assertEqual(func(), 1)
        f = gen_f()
        two, b, one, f_callee = f()
        self.assertEqual(one, 1)
        self.assertEqual(two, 2)
        self.assertIs(f, f_callee)
        self.assertEqual(b.__name__, 'a')
        self.assertIs(b, b())

    def test_runtime_error(self):
        source = '''
        def_(lambda b=1/0 if a==0 else 1: [
            if_[a == 1] [1/0
            ].elif_[a==2] [
                1/0
            ].elif_[a==3] [

            1/0] 
        ])()

        if a == 4:
            1/0

        f=def_(lambda
            b=1/0 if a == 5 else 0: [pass_])

        f()

        {stmt_bundles}
        
        if a == 6:
            1/0
        '''.format(stmt_bundles='var=1;' * 1000)

        def assert_error_at(a, lineno):
            try:
                self.assertRaises(NonexistantError, exec, code2, {'a': a})
            except ZeroDivisionError:
                _, _, tb = sys.exc_info()
                tb = traceback.extract_tb(tb)
                self.assertEqual(tb[-1].lineno, lineno, 'a={}'.format(a))

        _, code2 = self.makecode(source)
        for a, lineno in enumerate([1, 2, 4, 7, 11, 14, 21]):
            assert_error_at(a, lineno)


class NonexistantError(Exception):
    pass
