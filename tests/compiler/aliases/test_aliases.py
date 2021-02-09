import os
import sys
import importlib
import unittest

from astcheck import assert_ast_like

Def = None


def _reload_lambdex():
    for modname in sorted(filter(lambda x: 'lambdex' in x, sys.modules)):
        del sys.modules[modname]


class TestAliases(unittest.TestCase):
    def setUp(self):
        os.environ['LXALIAS'] = '1'
        _reload_lambdex()

        from lambdex import Def as d
        from lambdex.compiler import core

        global Def
        Def = d

        core.__DEBUG__ = True

    def tearDown(self):
        from lambdex.compiler import core
        core.__DEBUG__ = False

        del os.environ['LXALIAS']
        _reload_lambdex()

    def assert_ast_like(self, f, target):
        from lambdex.utils.ast import ast_from_source, pformat, pprint, recursively_set_attr
        ast_f = f.__ast__
        recursively_set_attr(ast_f, 'type_comment', None)
        ast_target = ast_from_source(target, 'def')
        ast_target.name = ast_f.name

        try:
            assert_ast_like(ast_f, ast_target)
        except AssertionError as cause:
            msg = '\n'.join(['', '===> Compiled:', pformat(ast_f), '===> Target:', pformat(ast_target)])
            raise AssertionError(msg) from cause

    def test_aliases(self):
        f = Def(lambda: [
            If[True] [
                a <= 1
            ].Else [
                a <= 2
            ]
        ])

        def target():
            if True:
                a = 1
            else:
                a = 2

        self.assert_ast_like(f, target)
