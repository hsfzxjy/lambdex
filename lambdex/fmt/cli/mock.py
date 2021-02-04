import os
import sys
import shutil
import argparse
from pathlib import Path
from textwrap import dedent

import inquirer

LAMBDEX_ROOT = Path(__file__).parent.parent.parent.parent
AUTO_GENERATED_COMMENT = b'auto generated by lambdex.fmt.cli.mock'
PREFIX = 'original_'

if os.name == 'nt':
    SCRIPT_TEMPLATE = '''
        @echo off
        REM {comment}
        setlocal
        set PYTHONPATH={lambdex_root};%PYTHONPATH% && {py_interpreter} -m lambdex.fmt %* -- -a {formatter_type} -e {formatter_path}
        endlocal
        @echo on
        '''
else:
    SCRIPT_TEMPLATE = '''
        #!/bin/sh
        # {comment}
        if [ -z $PYTHONPATH ]; then
            export PYTHONPATH={lambdex_root}
        else
            export PYTHONPATH={lambdex_root}:$PYTHONPATH
        fi
        {py_interpreter} -m lambdex.fmt $@ -- -a {formatter_type} -e {formatter_path}
        '''


def _script(formatter_type: str, formatter_path: Path) -> str:
    output = SCRIPT_TEMPLATE.format(
        py_interpreter=sys.executable,
        formatter_type=formatter_type,
        formatter_path=str(formatter_path),
        comment=AUTO_GENERATED_COMMENT.decode('utf-8'),
        lambdex_root=LAMBDEX_ROOT,
    )
    return dedent(output).strip()


def _save_script(path: Path, content: str):
    if os.name == 'nt':
        name = path.name.replace('.exe', '.cmd')
        path = path.parent / name

    path.write_text(content)

    if os.name != 'nt':
        path.chmod(0o775)


def _is_generated_script(path: Path) -> bool:
    with path.open('rb') as fd:
        content = fd.read()
        return AUTO_GENERATED_COMMENT in content


def _backup_executable(path: Path) -> Path:
    parent, name = path.parent, path.name
    new_name = PREFIX + name
    shutil.move(path, parent / new_name)
    return parent / new_name


def _restore_executable(path: Path):
    parent, name = path.parent, path.name
    if os.name == 'nt':
        name = name.replace('.cmd', '.exe')
    exe_name = PREFIX + name
    shutil.move(parent / exe_name, parent / name)


def _whereis(command: str):
    if os.name == 'nt':
        p = os.popen('where {}'.format(command))
        output = p.read().strip().split()
    else:
        p = os.popen('whereis {}'.format(command))
        output = p.read().strip().split()[1:]

    p.close()
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('CMD')
    parser.add_argument('-r', '--reset', action='store_true')
    opts = parser.parse_args()

    command = opts.CMD
    commands = [cmd for cmd in _whereis(command) if _is_generated_script(Path(cmd)) == opts.reset]

    questions = [
        inquirer.List(
            'path',
            message="Which one do you want to {}?".format('reset' if opts.reset else 'mock'),
            choices=commands,
        ),
    ]

    answers = inquirer.prompt(questions)
    if answers is None:
        return
    path = Path(answers['path'])

    if not opts.reset:
        backup_path = _backup_executable(path)
        _save_script(path, _script(opts.CMD, backup_path))
    else:
        _restore_executable(path)


if __name__ == '__main__':
    main()