import enum

__all__ = ['StackFrame']


class ContextFlag(enum.Enum):
    BODY = enum.auto()
    STMT = enum.auto()
    EXPR = enum.auto()
    CLAUSE = enum.auto()
    LAMBDEX = enum.auto()
    UNKNOWN = enum.auto()


class StackFrame:
    def __init__(self, flag, node):
        self.flag = flag
        self.node = node

    def _builder(item):
        return lambda self: self.flag == ContextFlag[item]

    for item in ContextFlag.__members__:
        locals()[f'is_{item.lower()}'] = property(_builder(item))

    def _builder(item):
        def _inner(cls, cond, node):
            flag = ContextFlag[item] if cond else ContextFlag.UNKNOWN

            return cls(flag, node)

        return _inner

    for item in ContextFlag.__members__:
        locals()[f'new_{item.lower()}_if'] = classmethod(_builder(item))

    def _builder(item):
        def _inner(cls, node):
            return cls(ContextFlag[item], node)

        return _inner

    for item in ContextFlag.__members__:
        locals()[f'new_{item.lower()}'] = classmethod(_builder(item))

    del _builder