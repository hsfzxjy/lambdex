import sys
import pathlib
import difflib
import unittest
import subprocess

TEST_DIR = pathlib.Path(__file__).parent


def _test_cases():
    fmt_samples_dir = TEST_DIR / 'fmt_samples'
    for src in fmt_samples_dir.glob('*.src.py'):
        dst = src.parent / src.name.replace('.src', '.dst')
        yield (src.name.replace('.', '_'), src, dst)


def _build_test_func(src, dst):
    def _func(self):
        p = subprocess.Popen(
            [sys.executable, '-m', 'lambdex.fmt', str(src.absolute())],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(TEST_DIR.parent.parent),
        )
        stdout, stderr = p.communicate()
        output = stdout.decode()
        desired_output = dst.read_text()
        self.assertEqual(p.returncode, 0, msg='STDERR:\n' + stderr.decode())
        self.assertEqual(output, desired_output)

    return _func


class TestFmtResult(unittest.TestCase):
    for name, src, dst in _test_cases():
        locals()[name] = _build_test_func(src, dst)
