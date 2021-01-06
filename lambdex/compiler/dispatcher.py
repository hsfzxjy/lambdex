import ast

from lambdex.utils.registry import FunctionRegistry
from .clauses import match_clauses
from .context import ContextFlag

__all__ = ['Dispatcher']

Dispatcher = FunctionRegistry('Dispatcher').set_default(lambda *_: None)


@Dispatcher.register(ast.Call)
def disp_Call(node: ast.Call, flag: ContextFlag):
    func = node.func

    if isinstance(func, ast.Name):
        name = func.id
    elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        name = func.value.id
    else:
        name = None

    return {
        'def_': ast.FunctionDef,
    }.get(name)


@Dispatcher.register(ast.Subscript)
def disp_Subscript(node: ast.Subscript, flag: ContextFlag):
    clauses = match_clauses(node)
    if clauses is None:
        return

    return {
        'return_': ast.Return,
        'if_': ast.If,
        'for_': ast.For,
        'while_': ast.While,
    }.get(clauses[0].name), clauses
