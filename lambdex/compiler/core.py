import ast
import types
import inspect
import functools

from .rules import Rules
from .context import Context, ContextFlag
from .dispatcher import Dispatcher

from lambdex.utils.ast import pformat, empty_arguments, None_node

__all__ = ['compile_lambdex']

__DEBUG__ = False


def compile_node(node, ctx, *, flag=ContextFlag.should_be_expr):

    if node is None:
        return None

    dispatcher = Dispatcher.get(node.__class__)
    rule_id, extra_args = dispatcher(node, flag)
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


def _wrap_code_object(code_obj, lambda_func, lambdex_ast_node):
    code_obj = code_obj.replace(co_freevars=lambda_func.__code__.co_freevars)

    ret = types.FunctionType(
        code_obj,
        lambda_func.__globals__,
        code_obj.co_name,
        lambda_func.__defaults__,
        lambda_func.__closure__,
    )

    if __DEBUG__:
        ret.__ast__ = lambdex_ast_node

    return ret


def compile_lambdex(declarer):
    lambda_ast = declarer.get_ast()
    lambda_func = declarer.func

    context = Context(
        compile_node,
        lambda_func.__globals__,
    )
    lambdex_node = compile_node(
        lambda_ast,
        ctx=context,
        flag=ContextFlag.outermost_lambdex,
    )

    freevars = lambda_func.__code__.co_freevars
    if freevars:
        wrapper_name = context.select_name_and_use('wrapper')
        wrapper_node = ast.FunctionDef(
            name=wrapper_name,
            args=empty_arguments,
            body=[
                ast.Assign(
                    targets=[ast.Name(id=name, ctx=ast.Store()) for name in freevars],
                    value=None_node,
                ),
                lambdex_node,
            ],
            decorator_list=[],
            returns=None,
        )
        module_node = ast.Module(
            body=[wrapper_node],
            type_ignores=[],
        )
    else:
        module_node = ast.Module(
            body=[lambdex_node],
            type_ignores=[],
        )
    module_node = ast.fix_missing_locations(module_node)

    if __DEBUG__:
        try:
            module_code = compile(module_node, '<lambdex>', 'exec')
        except Exception as e:
            raise SyntaxError(pformat(module_node)) from e
    else:
        module_code = compile(module_node, '<lambdex>', 'exec')

    if freevars:
        module_code = module_code.co_consts[0]

    for obj in module_code.co_consts:
        if inspect.iscode(obj) and obj.co_name == lambdex_node.name:
            lambdex_code = obj
            break

    return _wrap_code_object(lambdex_code, lambda_func, lambdex_node)
