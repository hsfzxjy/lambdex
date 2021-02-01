from typing import Optional
from dataclasses import dataclass


@dataclass
class Result:
    success: bool
    output: Optional[bytes] = None
