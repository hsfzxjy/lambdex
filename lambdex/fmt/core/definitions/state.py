import enum


class State(enum.Enum):
    UNKNOWN = enum.auto()

    EXPECT_LBDX_LPAR = enum.auto()
    EXPECT_LBDX_RPAR = enum.auto()
    MUST_LBDX_LPAR = enum.auto()
    EXPECT_LBDX_NAME = enum.auto()

    IN_LBDX_CALL = enum.auto()
    IN_LBDX_LAMBDA = enum.auto()
    IN_LBDX_BODY_LIST = enum.auto()
    IN_LBDX_CLS_HEAD = enum.auto()
    IN_LBDX_CLS_BODY = enum.auto()

    EXPECT_LBDX_LSQB = enum.auto()

    EXPECT_CLS_HEAD_LSQB = enum.auto()
    EXPECT_CLS_BODY_LSQB = enum.auto()
    EXPECT_SUBCLS_DOT = enum.auto()
    EXPECT_SUBCLS_NAME = enum.auto()
    MUST_SUBCLS_DOT_WITH_HEAD = enum.auto()
    MUST_SUBCLS_DOT_WITH_BODY = enum.auto()

    MUST_SUBCLS_NAME_WITH_HEAD = enum.auto()
    MUST_SUBCLS_NAME_WITH_BODY = enum.auto()

    EXPECT_CLS_HEAD_OR_BODY_LSQB = enum.auto()
    EXPECT_CLS_HEAD_OR_BODY_RSQB = enum.auto()

    EXPECT_CLS_MAYBE_BODY_LSQB = enum.auto()
