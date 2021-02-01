import enum


class Annotation(enum.Enum):

    DECL = enum.auto()
    DECL_LPAR = enum.auto()
    DECL_LAMBDA = enum.auto()

    BODY_LSQB = enum.auto()
    BODY_RSQB = enum.auto()

    CLS_DOT = enum.auto()
    CLS_DECL = enum.auto()

    CLS_HEAD_LSQB = enum.auto()
    CLS_HEAD_RSQB = enum.auto()

    CLS_BODY_LSQB = enum.auto()
    CLS_BODY_RSQB = enum.auto()

    STMT_COMMA = enum.auto()
    STMT_START = enum.auto()
    STMT_END = enum.auto()

    DECL_ARG_COMMA = enum.auto()
    DECL_RPAR = enum.auto()

    # Just behind the last comma or the last STMT_END
    LAST_STMT_WITH_COMMA = enum.auto()
    LAST_STMT_WITHOUT_COMMA = enum.auto()

    LAST_NL_BEFORE_RSQB = enum.auto()

    def __repr__(self) -> str:
        return self.name
