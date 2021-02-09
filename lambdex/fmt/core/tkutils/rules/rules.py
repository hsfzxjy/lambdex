# In this module, we use aliases in a lazy way.
from lambdex._aliases import _Aliases
from ...definitions import State, Context, TokenInfo, tk, A, actions

from .matcher import matcher as m


@m(exact_type=tk.LPAR)
@m(exact_type=tk.LSQB)
@m(exact_type=tk.LBRACE)
def r(ctx: Context, token: TokenInfo):
    ctx.push_op(token)


@m(exact_type=tk.RPAR)
@m(exact_type=tk.RSQB)
@m(exact_type=tk.RBRACE)
def r(ctx: Context, token: TokenInfo):
    ltoken, state = ctx.pop_op()
    if not tk.ISMATCHED(ltoken, token) or state != ctx.last_state:
        ctx.error()


@m(exact_type=tk.NAME, string=_Aliases.def_, last_state=State.UNKNOWN)
@m(exact_type=tk.NAME, string=_Aliases.def_, last_state=State.IN_LBDX_LAMBDA)
@m(exact_type=tk.NAME, string=_Aliases.def_, last_state=State.IN_LBDX_CLS_HEAD)
@m(exact_type=tk.NAME, string=_Aliases.def_, last_state=State.IN_LBDX_CLS_BODY)
@m(exact_type=tk.NAME, string=_Aliases.def_, last_state=State.IN_LBDX_BODY_LIST)
def r(ctx: Context, token: TokenInfo):
    ctx.push_state(State.EXPECT_LBDX_LPAR)

    ctx.cache = token
    return actions.StartBuffer()


@m(exact_type=tk.DOT, last_state=State.EXPECT_LBDX_LPAR)
def r(ctx: Context, token: TokenInfo):
    ctx.pop_state()
    ctx.push_state(State.EXPECT_LBDX_NAME)


@m(exact_type=tk.NAME, last_state=State.EXPECT_LBDX_NAME)
def r(ctx: Context, token: TokenInfo):
    ctx.pop_state()
    ctx.push_state(State.MUST_LBDX_LPAR)


@m(exact_type=tk.LPAR, last_state=State.MUST_LBDX_LPAR)
@m(exact_type=tk.LPAR, last_state=State.EXPECT_LBDX_LPAR)
def r(ctx: Context, token: TokenInfo):
    ctx.pop_state()

    ctx.cache.annotation = A.DECL
    ctx.push_state(State.IN_LBDX_CALL)
    token.annotation = A.DECL_LPAR
    ctx.push_op(token)
    return actions.StopBuffer()


@m(last_state=State.MUST_LBDX_LPAR)
@m(last_state=State.EXPECT_LBDX_LPAR)
def r(ctx: Context, token: TokenInfo):
    ctx.pop_state()
    ctx.cache = None
    return actions.StopBuffer(dont_consume=True)


@m(exact_type=tk.NAME, string='lambda', last_state=State.IN_LBDX_CALL)
def r(ctx: Context, token: TokenInfo):
    ctx.push_state(State.IN_LBDX_LAMBDA)
    token.annotation = A.DECL_LAMBDA


@m(exact_type=tk.COLON, last_state=State.IN_LBDX_LAMBDA)
def r(ctx: Context, token: TokenInfo):
    ctx.pop_state()
    ctx.push_state(State.EXPECT_LBDX_LSQB)


@m(exact_type=tk.LSQB, last_state=State.EXPECT_LBDX_LSQB)
def r(ctx: Context, token: TokenInfo):

    ctx.pop_state()
    ctx.push_state(State.IN_LBDX_BODY_LIST)
    token.annotation = A.BODY_LSQB
    ctx.push_op(token)
    ctx.push_ret(token)

    sentinel = TokenInfo.new_sentinel_after(token, A.STMT_START)
    ctx.push_ret(sentinel)

    return actions.Default(dont_store=True)


@m(exact_type=tk.COMMA, last_state=State.IN_LBDX_BODY_LIST)
def r(ctx: Context, token: TokenInfo):
    if ctx.last_op[0].annotation not in (A.BODY_LSQB, A.CLS_BODY_LSQB):
        return

    sentinel = TokenInfo.new_sentinel_before(token, A.STMT_END)
    ctx.push_ret(sentinel)

    token.annotation = A.STMT_COMMA
    ctx.push_ret(token)

    sentinel = TokenInfo.new_sentinel_after(token, A.STMT_START)
    ctx.push_ret(sentinel)

    return actions.Default(dont_store=True)


@m(exact_type=tk.RSQB, last_state=State.IN_LBDX_BODY_LIST)
def r(ctx: Context, token: TokenInfo):
    if ctx.pop_op()[0].annotation == A.BODY_LSQB:
        ctx.pop_state()
        ctx.push_state(State.EXPECT_LBDX_RPAR)

        sentinel = TokenInfo.new_sentinel_before(token, A.STMT_END)
        ctx.push_ret(sentinel)
        token.annotation = A.BODY_RSQB
        ctx.push_ret(token)
        return actions.Default(dont_store=True)


@m(exact_type=tk.RPAR, last_state=State.EXPECT_LBDX_RPAR)
def r(ctx: Context, token: TokenInfo):
    t, state = ctx.pop_op()
    if state not in (State.EXPECT_LBDX_LSQB, State.IN_LBDX_CALL) or not tk.ISMATCHED(t, token):
        ctx.error()

    if t.annotation == A.DECL_LPAR:
        ctx.pop_state()
        ctx.pop_state()
        token.annotation = A.DECL_RPAR


@m(exact_type=tk.COMMA, last_state=State.EXPECT_LBDX_RPAR)
def r(ctx: Context, token: TokenInfo):
    if ctx.last_op[0].annotation != A.DECL_LPAR:
        ctx.error()

    token.annotation = A.DECL_ARG_COMMA


@m(exact_type=tk.NAME, string=_Aliases.if_, last_state=State.IN_LBDX_BODY_LIST)
@m(exact_type=tk.NAME, string=_Aliases.with_, last_state=State.IN_LBDX_BODY_LIST)
@m(exact_type=tk.NAME, string=_Aliases.for_, last_state=State.IN_LBDX_BODY_LIST)
@m(exact_type=tk.NAME, string=_Aliases.while_, last_state=State.IN_LBDX_BODY_LIST)
@m(exact_type=tk.NAME, string=_Aliases.if_, last_state=State.IN_LBDX_CLS_BODY)
@m(exact_type=tk.NAME, string=_Aliases.with_, last_state=State.IN_LBDX_CLS_BODY)
@m(exact_type=tk.NAME, string=_Aliases.for_, last_state=State.IN_LBDX_CLS_BODY)
@m(exact_type=tk.NAME, string=_Aliases.while_, last_state=State.IN_LBDX_CLS_BODY)
def r(ctx: Context, token: TokenInfo):
    ctx.push_state(State.EXPECT_CLS_HEAD_LSQB)
    ctx.cache = [token]
    return actions.StartBuffer()


@m(exact_type=tk.LSQB, last_state=State.EXPECT_CLS_HEAD_LSQB)
def r(ctx: Context, token: TokenInfo):
    token.annotation = A.CLS_HEAD_LSQB
    ctx.push_op(token)
    ctx.pop_state()
    ctx.push_state(State.IN_LBDX_CLS_HEAD)

    _annotate_clause_declarer(ctx)
    ctx.cache = None
    if ctx.is_buffering():
        return actions.StopBuffer()


@m(last_state=State.EXPECT_CLS_HEAD_LSQB)
@m(last_state=State.EXPECT_CLS_BODY_LSQB)
def r(ctx: Context, token: TokenInfo):
    ctx.pop_state()
    ctx.cache = None
    return actions.StopBuffer()


@m(exact_type=tk.RSQB, last_state=State.IN_LBDX_CLS_HEAD)
def r(ctx: Context, token: TokenInfo):
    if ctx.pop_op()[1] == State.EXPECT_CLS_HEAD_LSQB:
        ctx.pop_state()
        ctx.push_state(State.EXPECT_CLS_BODY_LSQB)
        token.annotation = A.CLS_HEAD_RSQB


@m(exact_type=tk.NAME, string=_Aliases.try_, last_state=State.IN_LBDX_BODY_LIST)
@m(exact_type=tk.NAME, string=_Aliases.try_, last_state=State.IN_LBDX_CLS_BODY)
def r(ctx: Context, token: TokenInfo):
    ctx.push_state(State.EXPECT_CLS_BODY_LSQB)
    ctx.cache = [token]
    return actions.StartBuffer()


def _annotate_clause_declarer(ctx: Context):
    if ctx.cache is None:
        return actions.Default()
    if not isinstance(ctx.cache, list):
        ctx.error()
    length = len(ctx.cache)
    if length == 1:
        ctx.cache[0].annotation = A.CLS_DECL
    elif length == 2:
        ctx.cache[0].annotation = A.CLS_DOT
        ctx.cache[1].annotation = A.CLS_DECL
    else:
        ctx.error()


@m(exact_type=tk.LSQB, last_state=State.EXPECT_CLS_BODY_LSQB)
def r(ctx: Context, token: TokenInfo):
    if ctx.is_buffering():
        return actions.StopBuffer(dont_consume=True)

    ctx.pop_state()
    ctx.push_state(State.IN_LBDX_CLS_BODY)
    token.annotation = A.CLS_BODY_LSQB
    ctx.push_op(token)

    _annotate_clause_declarer(ctx)
    ctx.cache = None

    ctx.push_ret(token)
    sentinel = TokenInfo.new_sentinel_after(token, A.STMT_START)
    ctx.push_ret(sentinel)

    return actions.Default(dont_store=True)


@m(exact_type=tk.COMMA, last_state=State.IN_LBDX_CLS_BODY)
def r(ctx: Context, token: TokenInfo):
    sentinel = TokenInfo.new_sentinel_before(token, A.STMT_END)
    ctx.push_ret(sentinel)

    token.annotation = A.STMT_COMMA
    ctx.push_ret(token)

    sentinel = TokenInfo.new_sentinel_after(token, A.STMT_START)
    ctx.push_ret(sentinel)

    return actions.Default(dont_store=True)


@m(exact_type=tk.RSQB, last_state=State.IN_LBDX_CLS_BODY)
def r(ctx: Context, token: TokenInfo):
    if ctx.pop_op()[0].annotation == A.CLS_BODY_LSQB:
        ctx.pop_state()
        ctx.push_state(State.EXPECT_SUBCLS_DOT)

        sentinel = TokenInfo.new_sentinel_before(token, A.STMT_END)
        ctx.push_ret(sentinel)
        token.annotation = A.CLS_BODY_RSQB
        ctx.push_ret(token)
        return actions.Default(dont_store=True)


@m(exact_type=tk.DOT, last_state=State.EXPECT_SUBCLS_DOT)
@m(exact_type=tk.DOT, last_state=State.MUST_SUBCLS_DOT_WITH_HEAD)
@m(exact_type=tk.DOT, last_state=State.MUST_SUBCLS_DOT_WITH_BODY)
def r(ctx: Context, token: TokenInfo):
    last_state = ctx.pop_state()

    new_state = {
        State.EXPECT_SUBCLS_DOT: State.EXPECT_SUBCLS_NAME,
        State.MUST_SUBCLS_DOT_WITH_HEAD: State.MUST_SUBCLS_NAME_WITH_HEAD,
        State.MUST_SUBCLS_DOT_WITH_BODY: State.MUST_SUBCLS_NAME_WITH_BODY,
    }[last_state]

    ctx.push_state(new_state)
    ctx.cache = [token]

    return actions.StartBuffer()


@m(exact_type=tk.COMMA, last_state=State.EXPECT_SUBCLS_DOT)
def r(ctx: Context, token: TokenInfo):
    ctx.pop_state()
    sentinel = TokenInfo.new_sentinel_before(token, A.STMT_END)
    ctx.push_ret(sentinel)

    token.annotation = A.STMT_COMMA
    ctx.push_ret(token)

    sentinel = TokenInfo.new_sentinel_after(token, A.STMT_START)
    ctx.push_ret(sentinel)

    if ctx.is_buffering():
        return actions.StopBuffer(dont_store=True)

    return actions.Default(dont_store=True)


@m(last_state=State.EXPECT_SUBCLS_DOT)
def r(ctx: Context, token: TokenInfo):
    ctx.pop_state()
    if ctx.is_buffering():
        return actions.StopBuffer(dont_consume=True)
    return actions.Default(dont_consume=True)


@m(exact_type=tk.NAME, string=_Aliases.else_, last_state=State.EXPECT_SUBCLS_NAME)
@m(exact_type=tk.NAME, string=_Aliases.finally_, last_state=State.EXPECT_SUBCLS_NAME)
def r(ctx: Context, token: TokenInfo):
    ctx.pop_state()
    ctx.cache.append(token)
    ctx.push_state(State.EXPECT_CLS_BODY_LSQB)


@m(exact_type=tk.NAME, string=_Aliases.elif_, last_state=State.EXPECT_SUBCLS_NAME)
def r(ctx: Context, token: TokenInfo):
    ctx.pop_state()
    ctx.cache.append(token)
    ctx.push_state(State.EXPECT_CLS_HEAD_LSQB)


@m(exact_type=tk.NAME, string=_Aliases.except_, last_state=State.EXPECT_SUBCLS_NAME)
@m(exact_type=tk.NAME, string=_Aliases.except_, last_state=State.MUST_SUBCLS_NAME_WITH_HEAD)
@m(exact_type=tk.NAME, string=_Aliases.except_, last_state=State.MUST_SUBCLS_NAME_WITH_BODY)
def r(ctx: Context, token: TokenInfo):
    last_state = ctx.pop_state()
    ctx.cache.append(token)

    new_state = {
        State.EXPECT_SUBCLS_NAME: State.EXPECT_CLS_HEAD_OR_BODY_LSQB,
        State.MUST_SUBCLS_NAME_WITH_HEAD: State.EXPECT_CLS_HEAD_LSQB,
        State.MUST_SUBCLS_NAME_WITH_BODY: State.EXPECT_CLS_BODY_LSQB,
    }[last_state]

    ctx.push_state(new_state)


@m(exact_type=tk.LSQB, last_state=State.EXPECT_CLS_HEAD_OR_BODY_LSQB)
def r(ctx: Context, token: TokenInfo):
    ctx.push_op(token)
    ctx.pop_state()
    ctx.push_state(State.EXPECT_CLS_HEAD_OR_BODY_RSQB)


@m(last_state=State.EXPECT_CLS_HEAD_OR_BODY_LSQB)
def r(ctx: Context, token: TokenInfo):
    ctx.pop_state()
    return actions.StopBuffer()


@m(exact_type=tk.RSQB, last_state=State.EXPECT_CLS_HEAD_OR_BODY_RSQB)
def r(ctx: Context, token: TokenInfo):
    if ctx.pop_op()[1] == State.EXPECT_CLS_HEAD_OR_BODY_LSQB:
        ctx.pop_state()
        ctx.push_state(State.EXPECT_CLS_MAYBE_BODY_LSQB)


@m(exact_type=tk.LSQB, last_state=State.EXPECT_CLS_MAYBE_BODY_LSQB)
def r(ctx: Context, token: TokenInfo):
    return actions.Backtrace().state(State.MUST_SUBCLS_DOT_WITH_HEAD)


@m(last_state=State.EXPECT_CLS_MAYBE_BODY_LSQB)
def r(ctx: Context, token: TokenInfo):
    return actions.Backtrace().state(State.MUST_SUBCLS_DOT_WITH_BODY)
