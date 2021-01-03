import ast

from lambdex.utils.ast import *
from lambdex.utils.registry import FunctionRegistry

from .context import Context

__all__ = ['Rules']

Rules = FunctionRegistry('Rules')


@Rules.register(ast.FunctionDef)
def r_def(node: ast.Call, ctx: Context):
    check(node.args[0], ast.Lambda)
    lambda_: ast.Lambda = node.args[0]

    check(lambda_.body, ast.List)
    statements: ast.List = lambda_.body

    compiled_statements = []
    for statement in statements.elts:
        compiled_statement = ctx.compile(statement)
        if isinstance(compiled_statement, ast.expr):
            compiled_statement = ast.Expr(compiled_statement)

        compiled_statements.append(compiled_statement)

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
def r_return(node: ast.Subscript, ctx):
    value = value_from_subscript(node)
    return ast.Return(value=ctx.compile(value))
