from . import ast_parser, compiler, _aliases

aliases = _aliases.get_aliases()

__all__ = [aliases.def_, aliases.async_def_]


class Declarer:
    """
    This class serves as an entry of defining (transpiling) a lambdex.   Instances
    of `Declarer` can be attributed or called to form the syntax `<keyword>(<lambda>)`
    or `<keyword>.<ident>(<lambda>)`.
    """

    __slots__ = ['__keyword', '__identifier', 'func']

    def __init__(self, keyword):
        self.__identifier = None
        self.__keyword = keyword
        self.func = None

    def __getattr__(self, identifier: str):
        """
        Create a new `Declarer` instance with `self.__keyword` as keyword and `identifier`  
        as identifier.
        """
        if self.__identifier is not None:
            raise SyntaxError('Duplicated name {!r} and {!r}'.format(identifier, self.__identifier))

        if not identifier.isidentifier():
            raise SyntaxError('{!r} is not valid identifier'.format(identifier))

        ret = Declarer(self.__keyword)
        ret.__identifier = identifier

        return ret

    def get_ast(self):
        """
        Return the AST of `self.func`.

        This process requires `self.__keyword` and `self.__identifier` and thus can not be
        performed outside.
        """
        return ast_parser.lambda_to_ast(self.func, keyword=self.__keyword, identifier=self.__identifier)

    def __call__(self, f):
        """
        Transpile `f` into ordinary function and returns it.
        """
        self.func = f
        return compiler.compile_lambdex(self)

    def get_key(self):
        """
        Construct a unique key for `self.func`.
        """
        extra = ()
        if self.func is not None:
            code_obj = self.func.__code__
            extra = (code_obj.co_filename, code_obj.co_firstlineno, code_obj.co_code)

        return (self.__keyword, self.__identifier, *extra)


globals()[aliases.def_] = Declarer(aliases.def_)
globals()[aliases.async_def_] = Declarer(aliases.async_def_)
