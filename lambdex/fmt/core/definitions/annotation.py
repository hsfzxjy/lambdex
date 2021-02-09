import enum

from lambdex.utils import compat

auto = compat.enum_auto()


class Annotation(enum.Enum):

    DECL = auto()
    DECL_LPAR = auto()
    DECL_LAMBDA = auto()

    BODY_LSQB = auto()
    BODY_RSQB = auto()

    CLS_DOT = auto()
    CLS_DECL = auto()

    CLS_HEAD_LSQB = auto()
    CLS_HEAD_RSQB = auto()

    CLS_BODY_LSQB = auto()
    CLS_BODY_RSQB = auto()

    STMT_COMMA = auto()
    STMT_START = auto()
    STMT_END = auto()

    DECL_ARG_COMMA = auto()
    DECL_RPAR = auto()

    # Just behind the last comma or the last STMT_END
    LAST_STMT_WITH_COMMA = auto()
    LAST_STMT_WITHOUT_COMMA = auto()

    LAST_NL_BEFORE_RSQB = auto()

    def __repr__(self) -> str:
        return self.name


del auto