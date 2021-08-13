import os
import sys
import pathlib
import difflib
import unittest
import subprocess

TEST_DIR = pathlib.Path(__file__).parent


def _pad(string):
    if not string.endswith("\n"):
        string += "\n"
    return string


def _test_cases():
    fmt_samples_dir = TEST_DIR / "fmt_samples"
    for src in fmt_samples_dir.rglob("*.src.py"):
        dst = src.parent / src.name.replace(".src", ".dst")
        yield (src.name.replace(".", "_"), src, dst)


def _spawn_fmt(args):
    return subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(TEST_DIR.parent.parent),
        env=dict(LXALIAS="1", **os.environ),
    )


def _build_test_func(src, dst):
    def _func(self):
        self.maxDiff = None
        p = _spawn_fmt([sys.executable, "-m", "lambdex.fmt", str(src.absolute())])
        stdout, stderr = p.communicate()
        output = stdout.decode()
        desired_output = _pad(dst.read_text())
        self.assertEqual(p.returncode, 0, msg="STDERR:\n" + stderr.decode())
        self.assertEqual(output, desired_output, output)

    return _func


class TestFmtResult(unittest.TestCase):
    for name, src, dst in _test_cases():
        locals()[name] = _build_test_func(src, dst)

    def test_multi_files(self):
        self.maxDiff = None

        srcs = []
        dsts = []
        for _, src, dst in _test_cases():
            srcs.append(src)
            dsts.append(dst)

        p = _spawn_fmt(
            [sys.executable, "-m", "lambdex.fmt"] + [str(x.absolute()) for x in srcs]
        )
        stdout, stderr = p.communicate()
        output = stdout.decode()
        desired_output = "".join(map(_pad, map(pathlib.Path.read_text, dsts)))
        self.assertEqual(p.returncode, 0, msg="STDERR:\n" + stderr.decode())
        self.assertEqual(output, desired_output, output)
