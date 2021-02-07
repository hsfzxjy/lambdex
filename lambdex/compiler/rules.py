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
    ctx.assert_is_instance(node.body, ast.List, "expect '['")

    statements = node.body  # type: ast.List

    ctx.push_frame()

    ctx.assert_(statements.elts, 'empty body', statements)
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
    ctx.assert_(node.args, "expect 'lambda' in '()'", node.func)
    ctx.assert_is_instance(node.args[0], ast.Lambda, "expect 'lambda'")
    return r_lambda(node.args[0], ctx)


@Rules.register((ast.FunctionDef, ContextFlag.should_be_expr))
@Rules.register((ast.FunctionDef, ContextFlag.should_be_stmt))
def r_inner_def(node: ast.Call, ctx: Context):
    FunctionDef_node = r_def(node, ctx)
    ctx.frame.detached_functions.append(FunctionDef_node)

    return ast.Name(id=FunctionDef_node.name, ctx=ast.Load())


@Rules.register(ast.Return)
def r_return(node: ast.Subscript, ctx: Context, clauses: list):
    ctx.assert_clause_num_at_most(clauses, 1)
    clause = clauses[0]
    ctx.assert_no_head(clause)

    return copy_lineinfo(
        node,
        ast.Return(value=ctx.compile(clause.try_tuple_body())),
    )


@Rules.register(ast.If)
def r_if(node: ast.Subscript, ctx: Context, clauses: list):
    ctx.assert_head(clauses[0])
    ctx.assert_single_head(clauses[0])

    for clause in clauses[1:-1]:
        ctx.assert_name_equals(clause, 'elif_')
        ctx.assert_head(clause)
        ctx.assert_single_head(clause)

    if not clauses.single():
        clause = clauses[-1]
        ctx.assert_name_in(clause, ('else_', 'elif_'))
        if clause.name == 'else_':
            ctx.assert_no_head(clause)
        else:
            ctx.assert_head(clause)
            ctx.assert_single_head(clause)

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
    ctx.assert_clause_num_at_most(clauses, 2)

    ctx.assert_head(clauses[0])
    ctx.assert_single_head(clauses[0])
    if len(clauses) == 2:
        ctx.assert_name_equals(clauses[1], 'else_')
        ctx.assert_no_head(clauses[1])

    target, iter_item = check_compare(ctx, clauses[0].unwrap_head(), ast.In, 2)
    ctx.assert_lvalue(target)
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
    ctx.assert_clause_num_at_most(clauses, 2)

    ctx.assert_head(clauses[0])
    ctx.assert_single_head(clauses[0])
    if len(clauses) == 2:
        ctx.assert_name_equals(clauses[1], 'else_')
        ctx.assert_no_head(clauses[1])

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
    try:
        *targets, value = check_compare(ctx, node, ast.Lt)
    except SyntaxError:
        return copy_lineinfo(
            node,
            ast.Expr(ctx.compile(node, flag=ContextFlag.should_be_expr)),
        )

    for target in targets:
        ctx.assert_lvalue(target)
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
    ctx.assert_clause_num_at_most(clauses, 1)

    with_clause = clauses[0]
    ctx.assert_head(with_clause)

    items = []
    for arg in with_clause.head:
        context_expr, var = check_as(ctx, arg, ast.Gt)
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
    ctx.assert_clause_num_at_most(clauses, 2)

    raise_clause = clauses[0]
    ctx.assert_no_head(raise_clause)
    ctx.assert_single_body(raise_clause)
    exc = ctx.compile(raise_clause.unwrap_body())

    cause = None
    if len(clauses) == 2:
        from_clause = clauses[1]
        ctx.assert_name_equals(from_clause, 'from_')
        ctx.assert_no_head(from_clause)
        ctx.assert_single_body(from_clause)
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
    ctx.assert_no_head(try_clause)
    try_body = _compile_stmts(ctx, try_clause.body)

    handlers = []
    orelse_body = []
    final_body = []
    default_except_clause = None
    for clause in clauses[1:]:
        if clause.name == 'except_':
            ctx.assert_(
                not orelse_body and not final_body,
                "unexpected 'except_'",
                clause.node,
            )

            if clause.no_head():
                # bare except
                type_ = name = None
                default_except_clause = clause
            else:
                # except with capturing
                ctx.assert_(
                    default_except_clause is None,
                    "default 'except_' must be last",
                    lambda: default_except_clause.node,
                )
                ctx.assert_single_head(clause)
                type_, name = check_as(ctx, clause.unwrap_head(), ast.Gt, rhs_is_identifier=True)

            handler = ast.ExceptHandler(
                type=ctx.compile(type_),
                name=name,
                body=_compile_stmts(ctx, clause.body),
            )
            handlers.append(copy_lineinfo(clause.node, handler))
        elif clause.name == 'else_':
            ctx.assert_(
                handlers and not orelse_body and not final_body,
                "unexpected 'else_'",
                clause.node,
            )
            ctx.assert_no_head(clause)
            orelse_body.extend(_compile_stmts(ctx, clause.body))
        elif clause.name == 'finally_':
            ctx.assert_(
                not final_body,
                "unexpected 'finally_'",
                clause.node,
            )
            ctx.assert_no_head(clause)
            final_body.extend(_compile_stmts(ctx, clause.body))
        else:
            ctx.raise_('unexpected {!r}'.format(clause.name), clause.node)

    ctx.assert_(
        handlers or final_body,
        "'try_' has neither 'except_' clause(s) nor 'finally_' clause",
        try_clause.node,
    )

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
    ctx.assert_clause_num_at_most(clauses, 1)
    clause = clauses[0]
    ctx.assert_no_head(clause)

    return copy_lineinfo(
        node,
        rule_id(value=ctx.compile(clause.try_tuple_body())),
    )


@Rules.register(ast.Global)
@Rules.register(ast.Nonlocal)
def r_scoping(node: ast.Subscript, ctx: Context, clauses: list, rule_id):
    ctx.assert_clause_num_at_most(clauses, 1)
    clause = clauses[0]
    ctx.assert_no_head(clause)

    names = clause.body
    for name in names:
        ctx.assert_is_instance(name, ast.Name, "expect identifier")
    names = [name.id for name in names]

    return copy_lineinfo(
        node,
        rule_id(names=names),
    )
