import enum

from lambdex.utils import compat

auto = compat.enum_auto()


class State(enum.Enum):
    DISABLED = auto()
    UNKNOWN = auto()

    EXPECT_LBDX_LPAR = auto()
    EXPECT_LBDX_RPAR = auto()
    MUST_LBDX_LPAR = auto()
    EXPECT_LBDX_NAME = auto()

    IN_LBDX_CALL = auto()
    IN_LBDX_LAMBDA = auto()
    IN_LBDX_BODY_LIST = auto()
    IN_LBDX_CLS_HEAD = auto()
    IN_LBDX_CLS_BODY = auto()

    EXPECT_LBDX_LSQB = auto()

    EXPECT_CLS_HEAD_LSQB = auto()
    EXPECT_CLS_BODY_LSQB = auto()
    EXPECT_SUBCLS_DOT = auto()
    EXPECT_SUBCLS_NAME = auto()
    MUST_SUBCLS_DOT_WITH_HEAD = auto()
    MUST_SUBCLS_DOT_WITH_BODY = auto()

    MUST_SUBCLS_NAME_WITH_HEAD = auto()
    MUST_SUBCLS_NAME_WITH_BODY = auto()

    EXPECT_CLS_HEAD_OR_BODY_LSQB = auto()
    EXPECT_CLS_HEAD_OR_BODY_RSQB = auto()

    EXPECT_CLS_MAYBE_BODY_LSQB = auto()


del auto