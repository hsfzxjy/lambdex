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


@Dispatcher.register(ast.Name)
def disp_Name(node: ast.Name, flag: ContextFlag):
    if flag != ContextFlag.should_be_stmt:
        return

    rule_type = {
        'continue_': ast.Continue,
        'break_': ast.Break,
        'pass_': ast.Pass,
        'yield_': ast.Yield,
    }.get(node.id)

    if rule_type is not None:
        return 'single_keyword_stmt', rule_type

    return None


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
        'continue_': ast.Continue,
        'break_': ast.Break,
        'with_': ast.With,
        'raise_': ast.Raise,
        'try_': ast.Try,
        'pass_': ast.Pass,
        'yield_': ast.Yield,
        'yield_from_': ast.YieldFrom,
        'global_': ast.Global,
        'nonlocal_': ast.Nonlocal,
    }.get(clauses[0].name), clauses


@Dispatcher.register(ast.Compare)
def disp_Compare(node: ast.Compare, flag: ContextFlag):
    if flag != ContextFlag.should_be_stmt:
        return

    return ast.Assign
