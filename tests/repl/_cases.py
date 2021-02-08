import io
import re
import textwrap

import pexpect


def _remove_ANSI_escape(
    string: str,
    regexp=re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])'),
) -> str:
    """
    Remove ANSI escape sequence in a string.

    See https://stackoverflow.com/questions/14693701/
    """
    return regexp.sub('', string)


def get_output(inputs, *cmds, timeout=1):
    """
    Spawn a REPL, feed the inputs and get the outputs.
    """
    inputs = textwrap.dedent(inputs).strip()

    p = pexpect.spawn(*cmds)
    # Turn off ECHO so that they won't mess up the outputs
    p.setecho(False)

    # Save the stdout and stderr in `log`
    log = io.BytesIO()
    p.logfile_read = log

    for line in inputs.split('\n'):
        p.sendline(line.encode())

    try:
        p.expect(pexpect.EOF, timeout=timeout)
    except pexpect.TIMEOUT as exc:
        raise RuntimeError('OUTPUT:\n' + log.getvalue().decode()) from exc
    else:
        p.wait()

    return _remove_ANSI_escape(log.getvalue().decode())


class _Cases:
    def test_runtime_error(self):
        inputs = '''
        from lambdex.repl import *
        f = def_(lambda: [
            1 / 0, ])

        f()
        exit()
        '''

        outputs = '''
            1 / 0, ])
        ZeroDivisionError: division by zero
        >>> '''

        self._test(inputs, outputs)

    def test_compiletime_error(self):
        inputs = '''
        from lambdex.repl import *
        f = def_(lambda: [
            if_[a], ])

        exit()
        '''

        outputs = '''
           if_[a], ])
              ^
        SyntaxError: expect another group of '[]'
        >>> >>> '''

        self._test(inputs, outputs)
