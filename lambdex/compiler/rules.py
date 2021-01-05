import ast

from lambdex.utils.ast import *
from lambdex.utils.registry import FunctionRegistry

from .context import Context

__all__ = ['Rules']

Rules = FunctionRegistry('Rules')


def _compile_stmts(ctx: Context, stmts):
    compiled_statements = []
    for statement in stmts:
        compiled_statement = ctx.compile(statement)
        if isinstance(compiled_statement, ast.expr):
            compiled_statement = ast.Expr(compiled_statement)

        compiled_statements.append(compiled_statement)

    return compiled_statements


@Rules.register(ast.FunctionDef)
def r_def(node: ast.Call, ctx: Context):
    check(node.args[0], ast.Lambda)
    lambda_: ast.Lambda = node.args[0]

    check(lambda_.body, ast.List)
    statements: ast.List = lambda_.body

    compiled_statements = _compile_stmts(ctx, statements.elts)

    new_function = ast.FunctionDef(
        name=ctx.select_name_and_use('anonymous'),
        args=lambda_.args,
        body=compiled_statements,
        decorator_list=[],
        returns=None,
        type_comment=None,
    )

    return new_function


@Rules.register(ast.Return)
def r_return(node: ast.Subscript, ctx: Context, clauses: list):
    assert clauses.single()
    clause = clauses[0]
    assert clause.no_head() and clause.single_body()

    return ast.Return(value=ctx.compile(clause.unwrap_body()))


@Rules.register(ast.If)
def r_if(node: ast, ctx: Context, clauses: list):
    assert clauses[0].name == 'if_' and clauses[0].single_head()
    for clause in clauses[1:-1]:
        assert clause.name == 'elif_'
        assert clause.single_head()
    if not clauses.single():
        assert clauses[-1].name in ('else_', 'elif_')
        if clauses[-1].name == 'else_':
            assert clauses[-1].no_head()

    prev_orelse = curr_node = None
    for clause in clauses[::-1]:
        if clause.name == 'else_':
            prev_orelse = _compile_stmts(ctx, clause.body)
            continue

        # if_ or elif_
        curr_node = ast.If(
            test=clause.unwrap_head(),
            body=_compile_stmts(ctx, clause.body),
            orelse=prev_orelse,
        )
        prev_orelse = [curr_node]

    return curr_node
