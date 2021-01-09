import ast
from collections import namedtuple

from lambdex.utils.registry import FunctionRegistry
from .clauses import match_clauses
from .context import ContextFlag

__all__ = ['Dispatcher']

RuleMeta = namedtuple('RuleMeta', ['id', 'args'])
EMPTY_RULE = RuleMeta(None, ())
Dispatcher = FunctionRegistry('Dispatcher').set_default(lambda *_: EMPTY_RULE)


@Dispatcher.register(ast.Lambda)
def disp_Lambda(node: ast.Lambda, flag: ContextFlag):
    if flag != ContextFlag.outermost_lambdex:
        return EMPTY_RULE

    return RuleMeta((ast.Lambda, flag), ())


@Dispatcher.register(ast.Call)
def disp_Call(node: ast.Call, flag: ContextFlag):
    func = node.func

    if isinstance(func, ast.Name):
        name = func.id
    elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        name = func.value.id
    else:
        name = None

    ast_type = {
        'def_': ast.FunctionDef,
    }.get(name)
    return RuleMeta((ast_type, flag), ())


@Dispatcher.register(ast.Name)
def disp_Name(node: ast.Name, flag: ContextFlag):
    if flag == ContextFlag.should_be_expr:
        mapping = {
            'yield_': ast.Yield,
        }
    elif flag == ContextFlag.should_be_stmt:
        mapping = {
            'continue_': ast.Continue,
            'break_': ast.Break,
            'pass_': ast.Pass,
            'yield_': ast.Yield,
        }

    rule_type = mapping.get(node.id)

    if rule_type is not None:
        return RuleMeta('single_keyword_stmt', (rule_type, ))

    return RuleMeta(None, ())


@Dispatcher.register(ast.Subscript)
def disp_Subscript(node: ast.Subscript, flag: ContextFlag):
    clauses = match_clauses(node)
    if clauses is None:
        return RuleMeta(None, ())

    ast_type = {
        'return_': ast.Return,
        'if_': ast.If,
        'for_': ast.For,
        'while_': ast.While,
        'with_': ast.With,
        'raise_': ast.Raise,
        'try_': ast.Try,
        'yield_': ast.Yield,
        'yield_from_': ast.YieldFrom,
        'global_': ast.Global,
        'nonlocal_': ast.Nonlocal,
    }.get(clauses[0].name)

    return RuleMeta(ast_type, (clauses, ))


@Dispatcher.register(ast.Compare)
def disp_Compare(node: ast.Compare, flag: ContextFlag):
    if flag != ContextFlag.should_be_stmt:
        return RuleMeta(None, ())

    return RuleMeta(ast.Assign, ())
