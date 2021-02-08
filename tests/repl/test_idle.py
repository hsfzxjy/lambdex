import os
import sys
import time
import unittest
import textwrap
import threading
import multiprocessing

try:
    import idlelib
    del idlelib
except ImportError:
    IDLE_AVAILABLE = False
else:
    IDLE_AVAILABLE = True

sys.path.append(os.path.dirname(__file__))
from _cases import _Cases

EOF = -1


def _subprocess(Q_in: multiprocessing.Queue, Q_out: multiprocessing.Queue):
    """
    The entry point of IDLE process.  We hack everything here to avoid
    pollution in the host process.
    """
    # Reset the argv so that IDLE will open a clean console
    sys.argv[1:] = []

    if sys.version_info < (3, 6):
        from idlelib import PyShell as pyshell
    else:
        from idlelib import pyshell

    outputs = []

    class _PyShell(pyshell.PyShell):
        """
        Hack `pyshell.PyShell` to:

         - Record output string from the execution backend;
         - Remove the prompt at exiting.
        """
        def write(self, s, tags=()):
            outputs.append(s)
            return super(_PyShell, self).write(s, tags)

        def close(self):
            self.stop_readline()
            self.canceled = True
            self.closing = True
            return pyshell.EditorWindow.close(self)

    pyshell.PyShell = _PyShell

    # Start a thread for IDLE main looping
    th = threading.Thread(target=pyshell.main)
    th.start()
    # Wait until `pyshell.flish.pyshell` is ready
    while not hasattr(pyshell, 'flist') or pyshell.flist.pyshell is None:
        time.sleep(0.1)

    pyshell_object = pyshell.flist.pyshell
    while True:
        string = Q_in.get()
        if string == EOF:
            break

        # Set the string onto the editor
        pyshell_object.text.insert('insert', string)
        # Trigger logic in ENTER event
        pyshell_object.enter_callback('')

        # Wait until the editor is ready to get more inputs
        while pyshell_object.executing and not pyshell_object.reading:
            time.sleep(0.1)

    th.join()
    # Send out the outputs
    Q_out.put(outputs)


def get_output_from_idle(inputs) -> str:
    """
    Feed the inputs into an IDLE process, and returns the output as
    string.
    """
    input_lines = inputs = textwrap.dedent(inputs).strip().split('\n')

    Q_in = multiprocessing.Queue()
    Q_out = multiprocessing.Queue()
    p = multiprocessing.Process(target=_subprocess, args=(Q_in, Q_out))
    p.start()

    for line in input_lines:
        Q_in.put(line)
    Q_in.put(EOF)

    outputs = None
    while outputs is None:
        try:
            outputs = Q_out.get(block=False, timeout=1)
        except multiprocessing.queues.Empty:
            if not p.is_alive():
                raise RuntimeError('IDLE process gone')
            time.sleep(0.5)
        else:
            break
    p.join()
    return ''.join(outputs).replace('    \t', '')


@unittest.skipIf(not IDLE_AVAILABLE, 'IDLE not available')
class TestIDLE(unittest.TestCase, _Cases):
    def _test(self, inputs, outputs):
        self.maxDiff = None
        stdout = get_output_from_idle(inputs)
        outputs = textwrap.dedent(outputs).lstrip('\r\n')
        self.assertEqual(stdout[-len(outputs):], outputs, stdout)
