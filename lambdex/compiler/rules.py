import ast
import inspect
from functools import partial

from lambdex.utils.ast import *
from lambdex.utils.registry import FunctionRegistry

from .context import Context, ContextFlag

__all__ = ['Rules']


class RulesRegistry(FunctionRegistry):
    def get(self, key, default=FunctionRegistry._empty):
        f = super().get(key, default)

        if f is not None and 'rule_id' in inspect.signature(f).parameters:
            return partial(f, rule_id=key)

        return f


Rules = RulesRegistry('Rules')


def _compile_stmts(ctx: Context, stmts):
    compiled_statements = []
    for statement in stmts:
        compiled_statement = ctx.compile(statement, flag=ContextFlag.should_be_stmt)
        if isinstance(compiled_statement, ast.expr):
            compiled_statement = ast.Expr(compiled_statement)
        copy_lineinfo(statement, compiled_statement)

        compiled_statements.append(compiled_statement)

    return compiled_statements


@Rules.register((ast.Lambda, ContextFlag.outermost_lambdex))
def r_lambda(node: ast.Lambda, ctx: Context):
    check(node.body, ast.List)
    statements: ast.List = node.body

    ctx.push_frame()

    compiled_statements = _compile_stmts(ctx, statements.elts)
    detached_functions = ctx.frame.detached_functions

    new_function = ast.FunctionDef(
        name=ctx.select_name_and_use('anonymous'),
        args=node.args,
        body=detached_functions + compiled_statements,
        decorator_list=[],
        returns=None,
        type_comment=None,
    )
    copy_lineinfo(node, new_function)

    ctx.pop_frame()

    return new_function


@Rules.register(ast.Lambda)
def r_simple_lambda(node: ast.Call, ctx: Context):
    # For ordinary lambda, simply return it to early stop recursion
    return node


@Rules.register((ast.FunctionDef, ContextFlag.outermost_lambdex))
def r_def(node: ast.Call, ctx: Context):
    check(node.args[0], ast.Lambda)
    return r_lambda(node.args[0], ctx)


@Rules.register((ast.FunctionDef, ContextFlag.should_be_expr))
@Rules.register((ast.FunctionDef, ContextFlag.should_be_stmt))
def r_inner_def(node: ast.Call, ctx: Context):
    FunctionDef_node = r_def(node, ctx)
    ctx.frame.detached_functions.append(FunctionDef_node)

    return ast.Name(id=FunctionDef_node.name, ctx=ast.Load())


@Rules.register(ast.Return)
def r_return(node: ast.Subscript, ctx: Context, clauses: list):
    assert clauses.single()
    clause = clauses[0]
    assert clause.no_head()

    return copy_lineinfo(
        node,
        ast.Return(value=ctx.compile(clause.try_tuple_body())),
    )


@Rules.register(ast.If)
def r_if(node: ast.Subscript, ctx: Context, clauses: list):
    assert clauses[0].name == 'if_' and clauses[0].single_head()
    for clause in clauses[1:-1]:
        assert clause.name == 'elif_'
        assert clause.single_head()
    if not clauses.single():
        assert clauses[-1].name in ('else_', 'elif_')
        if clauses[-1].name == 'else_':
            assert clauses[-1].no_head()

    curr_node = None
    prev_orelse = []
    for clause in clauses[::-1]:
        if clause.name == 'else_':
            prev_orelse = _compile_stmts(ctx, clause.body)
            continue

        # if_ or elif_
        curr_node = ast.If(
            test=ctx.compile(clause.unwrap_head()),
            body=_compile_stmts(ctx, clause.body),
            orelse=prev_orelse,
        )
        copy_lineinfo(clause.node, curr_node)
        prev_orelse = [curr_node]

    return curr_node


@Rules.register(ast.For)
def r_for(node: ast.Subscript, ctx: Context, clauses: list):
    assert len(clauses) <= 2

    assert clauses[0].name == 'for_' and clauses[0].single_head()
    if len(clauses) == 2:
        assert clauses[1].name == 'else_' and clauses[1].no_head()

    target, iter_item = check_compare(clauses[0].unwrap_head(), ast.In, 2)
    assert is_lvalue(target)
    target.ctx = ast.Store()

    if len(clauses) == 2:
        else_stmts = _compile_stmts(ctx, clauses[1].body)
    else:
        else_stmts = []

    return copy_lineinfo(
        node,
        ast.For(
            target=target,
            iter=ctx.compile(iter_item),
            body=_compile_stmts(ctx, clauses[0].body),
            orelse=else_stmts,
        ),
    )


@Rules.register(ast.While)
def r_while(node: ast.Subscript, ctx: Context, clauses: list):
    assert len(clauses) <= 2

    assert clauses[0].name == 'while_' and clauses[0].single_head()
    if len(clauses) == 2:
        assert clauses[1].name == 'else_' and clauses[1].no_head()

    if len(clauses) == 2:
        else_stmts = _compile_stmts(ctx, clauses[1].body)
    else:
        else_stmts = []

    return copy_lineinfo(
        node,
        ast.While(
            test=ctx.compile(clauses[0].unwrap_head()),
            body=_compile_stmts(ctx, clauses[0].body),
            orelse=else_stmts,
        ),
    )


@Rules.register(ast.Assign)
def r_assign(node: ast.Compare, ctx: Context):
    *targets, value = check_compare(node, ast.Lt)

    for target in targets:
        assert is_lvalue(target)
        cast_to_lvalue(target)

    return copy_lineinfo(
        node,
        ast.Assign(
            targets=targets,
            value=ctx.compile(value),
        ),
    )


@Rules.register('single_keyword_stmt')
def r_single_keyword_stmt(node: ast.Name, ctx: Context, rule_type):
    if rule_type == ast.Yield:
        new_node = ast.Yield(value=None)

    elif rule_type == ast.Raise:
        new_node = ast.Raise(exc=None, cause=None)

    else:
        new_node = rule_type()

    return copy_lineinfo(node, new_node)


@Rules.register(ast.With)
def r_with(node: ast.Subscript, ctx: Context, clauses: list):
    assert clauses.single()
    with_clause = clauses[0]

    assert not with_clause.no_head()

    items = []
    for arg in with_clause.head:
        context_expr, var = check_as(arg, ast.Gt)
        item = ast.withitem(
            context_expr=ctx.compile(context_expr),
            optional_vars=var,
        )
        items.append(copy_lineinfo(arg, item))

    return copy_lineinfo(
        node,
        ast.With(
            items=items,
            body=_compile_stmts(ctx, with_clause.body),
        ),
    )


@Rules.register(ast.Raise)
def r_raise(node: ast.Subscript, ctx: Context, clauses: list):
    assert len(clauses) <= 2

    raise_clause = clauses[0]
    assert raise_clause.no_head() and raise_clause.single_body()
    exc = ctx.compile(raise_clause.unwrap_body())

    cause = None
    if len(clauses) == 2:
        from_clause = clauses[1]
        assert from_clause.name == 'from_' and from_clause.no_head() and from_clause.single_body()
        cause = ctx.compile(from_clause.unwrap_body())

    return copy_lineinfo(
        node,
        ast.Raise(
            exc=exc,
            cause=cause,
        ),
    )


@Rules.register(ast.Try)
def r_try(node: ast.Subscript, ctx: Context, clauses: list):
    try_clause = clauses[0]
    assert try_clause.no_head()
    try_body = _compile_stmts(ctx, try_clause.body)

    handlers = []
    orelse_body = []
    final_body = []
    for clause in clauses[1:]:
        if clause.name == 'except_':
            assert not orelse_body and not final_body

            if clause.no_head():
                # bare except
                type_ = name = None
            else:
                # except with capturing
                assert clause.single_head()
                type_, name = check_as(clause.unwrap_head(), ast.Gt, rhs_is_identifier=True)

            handler = ast.ExceptHandler(
                type=ctx.compile(type_),
                name=name,
                body=_compile_stmts(ctx, clause.body),
            )
            handlers.append(copy_lineinfo(clause.node, handler))
        elif clause.name == 'else_':
            assert not orelse_body and not final_body
            assert clause.no_head()
            orelse_body.extend(_compile_stmts(ctx, clause.body))
        elif clause.name == 'finally_':
            assert not final_body
            final_body.extend(_compile_stmts(ctx, clause.body))

    return copy_lineinfo(
        node,
        ast.Try(
            body=try_body,
            handlers=handlers,
            orelse=orelse_body,
            finalbody=final_body,
        ),
    )


@Rules.register(ast.Yield)
@Rules.register(ast.YieldFrom)
def r_yield(node: ast.Subscript, ctx: Context, clauses: list, rule_id):
    assert clauses.single()
    clause = clauses[0]
    assert clause.no_head()

    return copy_lineinfo(
        node,
        rule_id(value=ctx.compile(clause.try_tuple_body())),
    )


@Rules.register(ast.Global)
@Rules.register(ast.Nonlocal)
def r_scoping(node: ast.Subscript, ctx: Context, clauses: list, rule_id):
    assert clauses.single()
    clause = clauses[0]
    assert clause.no_head()

    names = clause.body
    assert all(isinstance(name, ast.Name) for name in names)
    names = [name.id for name in names]

    return copy_lineinfo(
        node,
        rule_id(names=names),
    )
