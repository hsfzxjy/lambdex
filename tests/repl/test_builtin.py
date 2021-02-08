import os
import io
import sys
import time
import unittest
import textwrap

import pexpect

sys.path.append(os.path.dirname(__file__))
from _cases import _Cases, get_output


class TestBuiltinREPL(unittest.TestCase, _Cases):
    def _test(self, inputs, outputs):
        self.maxDiff = None
        outputs = textwrap.dedent(outputs)
        outputs = outputs.lstrip('\r\n').replace('\n', '\r\n')
        stdout = get_output(inputs, sys.executable, ['-i'])
        self.assertEqual(stdout[-len(outputs):], outputs, stdout)
