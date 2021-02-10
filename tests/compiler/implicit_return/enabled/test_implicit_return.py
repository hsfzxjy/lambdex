import sys
import importlib
import unittest

from astcheck import assert_ast_like


def _reload_lambdex():
    for modname in sorted(filter(lambda x: 'lambdex' in x, sys.modules)):
        del sys.modules[modname]


async_def_ = None


class TestImplicitReturn(unittest.TestCase):
    def setUp(self):
        _reload_lambdex()

        from lambdex import async_def_ as d
        from lambdex.compiler import core

        global async_def_
        async_def_ = d

        core.__DEBUG__ = True

    def tearDown(self):
        from lambdex.compiler import core
        core.__DEBUG__ = False

        _reload_lambdex()

    def assert_ast_like(self, f, target):
        from lambdex.utils.ast import ast_from_source, pformat, pprint, recursively_set_attr
        ast_f = f.__ast__
        recursively_set_attr(ast_f, 'type_comment', None)
        ast_target = ast_from_source(target, 'async def')
        ast_target.name = ast_f.name

        try:
            assert_ast_like(ast_f, ast_target)
        except AssertionError as cause:
            msg = '\n'.join(['', '===> Compiled:', pformat(ast_f), '===> Target:', pformat(ast_target)])
            raise AssertionError(msg) from cause

    def test_implicit_return_last_expr(self):
        f = async_def_(lambda: [
            1
        ])

        async def target():
            return 1

        self.assert_ast_like(f, target)

    def test_implicit_return_last_stmt(self):
        f = async_def_(lambda: [
            for_[a in b] [
                c
            ]
        ])

        async def target():
            for a in b:
                c

        self.assert_ast_like(f, target)

    def test_implicit_return_last_assignment(self):
        f = async_def_(lambda: [
            a < 1
        ])

        async def target():
            a = 1

        self.assert_ast_like(f, target)
