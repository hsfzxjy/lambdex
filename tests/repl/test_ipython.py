import os
import sys
import textwrap
import unittest

sys.path.append(os.path.dirname(__file__))
from _cases import _Cases, get_output


class TestIPython(unittest.TestCase, _Cases):
    def _test(self, inputs, outputs):
        self.maxDiff = None
        outputs = textwrap.dedent(outputs)
        outputs = outputs.lstrip('\r\n')
        stdout = get_output(
            inputs,
            sys.executable,
            ['-m', 'IPython', '--quiet', '--classic', '--quick', '--no-confirm-exit'],
            timeout=10,
        )
        for line in outputs.splitlines(keepends=False):
            if not line or '>>>' in line: continue
            self.assertTrue(line in stdout, '\n{!r} not in\n{}'.format(repr(line), stdout))
