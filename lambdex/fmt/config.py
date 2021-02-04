import typing
from dataclasses import dataclass, field

from .utils.logger import getLogger

logger = getLogger(__name__)


@dataclass
class Config:
    adapter: str

    quiet: bool = False
    in_place: bool = False
    print_diff: bool = False

    parallel: bool = False

    files: typing.List[str] = field(default_factory=list)

    @property
    def from_stdin(self):
        return not self.files
