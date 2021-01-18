from . import ast_parser, compiler

__all__ = ['def_']


class Declarer:

    __slots__ = ['__keyword', '__identifier', 'func']

    def __init__(self, keyword):
        self.__identifier = None
        self.__keyword = keyword
        self.func = None

    def __getattr__(self, identifier: str):
        if self.__identifier is not None:
            raise SyntaxError('Duplicated name {!r} and {!r}'.format(identifier, self.__identifier))

        if not identifier.isidentifier():
            raise SyntaxError('{!r} is not valid identifier'.format(identifier))

        ret = Declarer(self.__keyword)
        ret.__identifier = identifier

        return ret

    def get_ast(self):
        return ast_parser.lambda_to_ast(self.func, keyword=self.__keyword, identifier=self.__identifier)

    def __call__(self, f):
        self.func = f
        return compiler.compile_lambdex(self)

    def get_key(self):
        extra = ()
        if self.func is not None:
            code_obj = self.func.__code__
            extra = (code_obj.co_filename, code_obj.co_firstlineno, code_obj.co_code)

        return (self.__keyword, self.__identifier, *extra)


def_ = Declarer('def_')
