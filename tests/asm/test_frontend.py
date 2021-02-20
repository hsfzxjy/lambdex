import os.path as osp
import sys
import dis
import unittest
import importlib

import lambdex
from lambdex import asmopt
from lambdex.compiler.asm import frontend


class TestFrontend(unittest.TestCase):
    def setUp(self):
        self.old_path = sys.path
        sys.path = [osp.dirname(__file__)] + sys.path

        self.old_def_ = lambdex.def_
        frontend._done_queue = frontend.SimpleQueue()

    def tearDown(self):
        sys.path = self.old_path
        lambdex.def_ = self.old_def_
        frontend._done_queue = None

    def test_module(self):

        lambdex.def_ = None
        with self.assertRaises(TypeError):
            import sample

        lambdex.def_ = self.old_def_
        import sample
        self.assertEqual(sample.s, 4950)

        self.assertEqual(frontend._done_queue.get(), (sample.__file__, 'ok'))

        lambdex.def_ = None
        sample = importlib.reload(sample)
        self.assertEqual(sample.s, 4950)

    def test_asmopt(self):
        var = 1

        @asmopt
        def f():
            var2 = 3
            a = def_.a(lambda: [
                nonlocal_[var], 
                var < var + var2, 
                return_[callee_]
            ])
            b = def_.b(lambda: [
                nonlocal_[var], 
                var < var * var2, 
                return_[callee_]
            ])
            c = def_.c(lambda i: [
                nonlocal_[var], 
                var < var + i, 
                return_[callee_]
            ])
            return a, b, c

        # import dis
        # dis.dis(f)
        a, b, c = f()
        ca = a()
        self.assertEqual(var, 4)
        self.assertIs(a, ca)
        cb = b()
        self.assertEqual(var, 12)
        self.assertIs(b, cb)
        cc = c(1)
        self.assertEqual(var, 13)
        self.assertIs(c, cc)
