from . import ast_parser, compiler

__all__ = ['def_']


class KeywordWithOptionalName:

    __slots__ = ['__keyword', '__identifier']

    def __init__(self, keyword):
        self.__identifier = None
        self.__keyword = keyword

    def __getattr__(self, identifier: str):
        if self.__identifier is not None:
            raise SyntaxError('Duplicated name {!r} and {!r}'.format(identifier, self.__identifier))

        if not identifier.isidentifier():
            raise SyntaxError('{!r} is not valid identifier'.format(identifier))

        ret = KeywordWithOptionalName(self.__keyword)
        ret.__identifier = identifier

        return ret

    def __call__(self, f):
        lambda_ast = ast_parser.lambda_to_ast(f, keyword=self.__keyword, identifier=self.__identifier)
        return compiler.compile_lambdex(lambda_ast, f)


def_ = KeywordWithOptionalName('def_')