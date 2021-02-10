import ast
import types
import inspect
import functools

from .rules import Rules
from .context import Context, ContextFlag
from .dispatcher import Dispatcher
from . import cache

from lambdex.utils.ast import pformat, empty_arguments, None_node
from lambdex.utils import compat

__all__ = ['compile_lambdex']

# This flag is used internally. when turned on:
#  - compiled lambdex will have attribute `__ast__`
#  - verbose message are printed when error occurs during compiling
__DEBUG__ = False


def compile_node(node, ctx, *, flag=ContextFlag.should_be_expr):
    """
    Compile an AST node `node` to transpile lambdex syntax to Python lambdex.
    """
    if node is None:
        return None

    dispatcher = Dispatcher.get(node.__class__)
    rule_id, extra_args = dispatcher(node, ctx, flag)
    rule = Rules.get(rule_id, None)

    if rule is not None:
        return rule(node, ctx, *extra_args)

    # If no rule found, recursively compile children of `node`
    for field, old_value in ast.iter_fields(node):
        if isinstance(old_value, list):
            new_values = []
            for value in old_value:
                if isinstance(value, ast.AST):
                    value = compile_node(value, ctx)

                    if value is None:
                        # Discard from `new_values`
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
    """
    Construct a function using `code_obj`.

    To ensure the two functions have same context, the returned function
    copies `__globals__`, `__defaults__`, `__closure__` from `lambda_func`,
    with code object whose `co_freevars` copied from
    `lambda_func.__code__.co_freevars`.
    """

    # Append code object name to its co_freevars, so that lambdex
    # can always access itself via its name `anonymous_...`
    name = code_obj.co_name
    code_obj = compat.code_replace(
        code_obj,
        co_freevars=lambda_func.__code__.co_freevars + (name, ),
    )

    # Trick: Obtain a cell object referencing current function, by
    # constructing a new function and extract its closure.
    callee_ref_cells = (lambda: ret).__closure__

    # We should append a cell referencing current function to the new closure.
    if lambda_func.__closure__ is None:
        new_closure = callee_ref_cells
    else:
        new_closure = lambda_func.__closure__ + callee_ref_cells

    ret = types.FunctionType(
        code=code_obj,
        globals=lambda_func.__globals__,
        name=name,
        argdefs=lambda_func.__defaults__,
        closure=new_closure,
    )

    if __DEBUG__:
        ret.__ast__ = lambdex_ast_node

    return ret


def compile_lambdex(declarer):
    """
    Compile a lambda object given by `declarer` into a function.

    Multiple calls with a same declarer yield functions with same code object,
    whilst there closure and globals may be different.
    """
    # If cache hit, simply update metadata and return
    cached_value = cache.get(declarer)
    if cached_value is not None:
        code_obj, lambdex_ast_node = cached_value
        return _wrap_code_object(code_obj, declarer.func, lambdex_ast_node)

    # Otherwise, we have to compile from scratch

    lambda_ast = declarer.get_ast()
    lambda_func = declarer.func

    context = Context(
        compile_node,
        lambda_func.__globals__,
        lambda_func.__code__.co_filename,
    )
    lambdex_node = compile_node(
        lambda_ast,
        ctx=context,
        flag=ContextFlag.outermost_lambdex,
    )

    freevars = lambda_func.__code__.co_freevars  # name of nonlocal variables
    # A name in `lambdex_node` should be compiled as nonlocal instead of
    # global (default) if it appears in `freevars`.
    #
    # This is done by wrapping `lambdex_node` in another FunctionDef, and
    # let names in `freevars` become local variables in the wrapper.
    wrapper_name = context.select_name_and_use('wrapper')
    if freevars:
        wrapper_body = [
            ast.Assign(
                targets=[ast.Name(id=name, ctx=ast.Store()) for name in freevars],
                value=None_node,
            ),
            lambdex_node,
        ]
    else:
        wrapper_body = [lambdex_node]

    wrapper_node = ast.FunctionDef(
        name=wrapper_name,
        args=empty_arguments,
        body=wrapper_body,
        decorator_list=[],
        returns=None,
    )
    module_node = ast.Module(
        body=[wrapper_node],
        type_ignores=[],
    )
    module_node = ast.fix_missing_locations(module_node)

    if __DEBUG__:
        try:
            module_code = compile(module_node, lambda_func.__code__.co_filename, 'exec')
        except Exception as e:
            raise SyntaxError(pformat(module_node)) from e
    else:
        module_code = compile(module_node, lambda_func.__code__.co_filename, 'exec')

    # unwrap the outer FunctionDef.
    # since no other definition in the module, it should be co_consts[0]
    wrapper_code = module_code.co_consts[0]

    # the desired code object should be in `module_code.co_consts`
    # we use `.co_name` to identify
    for obj in wrapper_code.co_consts:
        if inspect.iscode(obj) and obj.co_name == lambdex_node.name:
            lambdex_code = obj
            break

    cache.set(declarer, (lambdex_code, lambdex_node))
    return _wrap_code_object(lambdex_code, lambda_func, lambdex_node)
