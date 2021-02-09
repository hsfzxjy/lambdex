from ...definitions import tk, TokenInfo

# A sentinel indicating an empty argument for `_make_key()`
_empty = object()


def _make_key(exact_type, string, last_state, *, strict=True):
    if exact_type == tk.NAME:
        return (exact_type, string, last_state)
    else:
        if strict: assert string is _empty
        return (exact_type, last_state)


def _generate_queries(token, last_state, keyword_to_symbol):

    symbol = keyword_to_symbol.get(token.string, token.string)

    # Use both `token` and `last_state`
    yield _make_key(token.exact_type, symbol, last_state, strict=False)

    # Use `token` and `last_state`, but ignore `symbol`
    # This is for the case you want to capture a `tk.NAME`, but don't care about its content
    yield _make_key(token.exact_type, _empty, last_state, strict=False)

    # Use only `last_state`
    yield _make_key(_empty, _empty, last_state, strict=False)

    # Use only `token`
    yield _make_key(token.exact_type, symbol, _empty, strict=False)


class Matcher:
    def __init__(self):
        self._mapping = {}
        self._keyword_to_symbol = {}

    def reset_aliases(self, *userpaths):
        from lambdex._aliases import _Aliases, get_aliases
        aliases = get_aliases(userpaths, reinit=True)

        self._keyword_to_symbol = {}
        for name, value in aliases._asdict().items():
            self._keyword_to_symbol[value] = getattr(_Aliases, name)

    def __call__(self, *, exact_type=_empty, string=_empty, last_state=_empty):
        def _inner(f):
            key = _make_key(exact_type, string, last_state)
            assert key not in self._mapping
            self._mapping[key] = f
            return f

        return _inner

    def dispatch(self, ctx, token):
        if token.is_WS_NL_CMT:
            # If token is whitespace, newline or comments, pass through
            return None

        for query in _generate_queries(token, ctx.last_state, self._keyword_to_symbol):
            if query in self._mapping:
                return self._mapping[query](ctx, token)

        else:
            # If all queries fail, pass through
            return None


matcher = Matcher()