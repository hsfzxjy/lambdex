import typing
from dataclasses import dataclass, field


@dataclass
class Config:
    adapter: str
    inplace: bool = False
    parallel: bool = False
    print_diff: bool = False
    files: typing.List[str] = field(default_factory=list)

    @property
    def from_stdin(self):
        return not self.files

    def validate(self):
        if len(self.files) > 1 and self.inplace:
            raise RuntimeError
