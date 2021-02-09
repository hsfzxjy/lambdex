import ast
from collections import namedtuple

from lambdex._aliases import get_aliases
aliases = get_aliases()

from lambdex.utils.registry import FunctionRegistry
from .clauses import match_clauses
from .context import ContextFlag, Context

__all__ = ['Dispatcher']

RuleMeta = namedtuple('RuleMeta', ['id', 'args'])
EMPTY_RULE = RuleMeta(None, ())
Dispatcher = FunctionRegistry('Dispatcher').set_default(lambda *_: EMPTY_RULE)


@Dispatcher.register(ast.Lambda)
def disp_Lambda(node: ast.Lambda, ctx: Context, flag: ContextFlag):
    if flag != ContextFlag.outermost_lambdex:
        return RuleMeta(ast.Lambda, ())

    return RuleMeta((ast.Lambda, flag), ())


@Dispatcher.register(ast.Call)
def disp_Call(node: ast.Call, ctx: Context, flag: ContextFlag):
    func = node.func

    if isinstance(func, ast.Name):
        name = func.id
    elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        name = func.value.id
    else:
        name = None

    ast_type = {
        aliases.def_: ast.FunctionDef,
    }.get(name)
    return RuleMeta((ast_type, flag), ())


@Dispatcher.register(ast.Name)
def disp_Name(node: ast.Name, ctx: Context, flag: ContextFlag):
    if flag == ContextFlag.should_be_expr:
        mapping = {
            aliases.yield_: ast.Yield,
        }
    elif flag == ContextFlag.should_be_stmt:
        mapping = {
            aliases.continue_: ast.Continue,
            aliases.break_: ast.Break,
            aliases.pass_: ast.Pass,
            aliases.yield_: ast.Yield,
            aliases.raise_: ast.Raise,
            aliases.return_: ast.Return,
        }

    rule_type = mapping.get(node.id)

    if rule_type is not None:
        return RuleMeta('single_keyword_stmt', (rule_type, ))

    return RuleMeta(None, ())


@Dispatcher.register(ast.Subscript)
def disp_Subscript(node: ast.Subscript, ctx: Context, flag: ContextFlag):
    clauses = match_clauses(node, ctx.raise_)
    if clauses is None:
        return RuleMeta(None, ())

    ast_type = {
        aliases.return_: ast.Return,
        aliases.if_: ast.If,
        aliases.for_: ast.For,
        aliases.while_: ast.While,
        aliases.with_: ast.With,
        aliases.raise_: ast.Raise,
        aliases.try_: ast.Try,
        aliases.yield_: ast.Yield,
        aliases.yield_from_: ast.YieldFrom,
        aliases.global_: ast.Global,
        aliases.nonlocal_: ast.Nonlocal,
    }.get(clauses[0].name)

    return RuleMeta(ast_type, (clauses, ))


@Dispatcher.register(ast.Compare)
def disp_Compare(node: ast.Compare, ctx: Context, flag: ContextFlag):
    if flag != ContextFlag.should_be_stmt:
        return RuleMeta(None, ())

    return RuleMeta(ast.Assign, ())
