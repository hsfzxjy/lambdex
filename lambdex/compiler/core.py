import ast
import functools

from .rules import Rules
from .context import Context, ContextFlag
from .dispatcher import Dispatcher

from lambdex.utils.ast import pprint

__all__ = ['compile_lambdex']


def compile_node(node, ctx, *, flag=ContextFlag.unset):

    dispatcher = Dispatcher.get(node.__class__)
    rule_meta = dispatcher(node, flag)
    if isinstance(rule_meta, tuple):
        rule_id, *extra_args = rule_meta
    else:
        rule_id = rule_meta
        extra_args = ()
    rule = Rules.get(rule_id, None)

    if rule is not None:
        return rule(node, ctx, *extra_args)

    for field, old_value in ast.iter_fields(node):
        if isinstance(old_value, list):
            new_values = []
            for value in old_value:
                if isinstance(value, ast.AST):
                    value = compile_node(value, ctx)
                    if value is None:
                        continue
                    elif not isinstance(value, ast.AST):
                        new_values.extend(value)
                        continue
                new_values.append(value)
            old_value[:] = new_values
        elif isinstance(old_value, ast.AST):
            new_node = compile_node(old_value, ctx)
            if new_node is None:
                delattr(node, field)
            else:
                setattr(node, field, new_node)

    return node


def compile_lambdex(lambda_ast, lambda_func):
    lambda_node = compile_node(
        lambda_ast,
        ctx=Context(
            compile_node,
            lambda_func.__globals__,
        ),
    )
    module_node = ast.Module(
        body=[lambda_node],
        type_ignores=[],
    )
    pprint(module_node)
    module_node = ast.fix_missing_locations(module_node)
    code = compile(module_node, '<lambdex>', 'exec')
    locals_ = {}
    exec(code, lambda_func.__globals__, locals_)
    ret = locals_[lambda_node.name]
    return ret