import abc
import sys
import difflib
import pathlib
from io import BytesIO

from ..jobs_meta import JobsMeta


def get_stdin() -> bytes:
    contents = []
    while True:
        if sys.stdin.closed:
            break
        try:
            content = sys.stdin.buffer.read()
            if not content: break
            contents.append(content)
        except EOFError:
            break
        except KeyboardInterrupt:
            sys.exit(1)

    return b''.join(contents)


class _ResourceBase(abc.ABC):
    def __init__(self, jobs_meta: JobsMeta):
        self._meta = jobs_meta
        self._source = self._get_source()
        self._backend_output_stream = None

    @abc.abstractmethod
    def _get_source(self) -> bytes:
        ...

    @abc.abstractmethod
    def _display_filename(self) -> str:
        ...

    @property
    def source(self):
        return self._source

    def set_backend_output(self, output: bytes):
        self._backend_output_stream = BytesIO(output)

    @property
    def backend_output_stream(self) -> BytesIO:
        assert self._backend_output_stream is not None
        return self._backend_output_stream

    def is_changed(self, formatted_code: str) -> bool:
        return self._source.decode('utf-8') != formatted_code

    def write_formatted_code(self, formatted_code: str):
        content = formatted_code
        if self._meta.print_diff:
            before = self._source.decode('utf-8').splitlines()
            after = formatted_code.splitlines()
            content = '\n'.join(
                difflib.unified_diff(
                    before,
                    after,
                    self._display_filename(),
                    self._display_filename(),
                    '(original)',
                    '(reformatted)',
                    lineterm='',
                )
            ) + '\n'
        elif not self._meta.in_place and not content.endswith('\n'):
            content += '\n'

        self._write_content(content)


class StdinResource(_ResourceBase):
    def _get_source(self) -> bytes:
        return get_stdin()

    def _display_filename(self) -> str:
        return '<stdin>'

    def _write_content(self, content: str):
        assert not self._meta.in_place
        if not self._meta.quiet:
            sys.stdout.write(content)


class FileResource(_ResourceBase):
    def __init__(self, jobs_meta: JobsMeta, filename: str):
        self._filename = filename
        self._filepath = pathlib.Path(filename)
        super(FileResource, self).__init__(jobs_meta)

    def _get_source(self) -> bytes:
        return self._filepath.read_bytes()

    def _display_filename(self) -> str:
        return self._filename

    def _write_content(self, content: str):
        if self._meta.in_place:
            self._filepath.write_text(content)
        elif not self._meta.quiet:
            sys.stdout.write(content)
