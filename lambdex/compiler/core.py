import ast
import types
import typing
import inspect
import functools

from ..utils import compat
from .rules import Rules
from .context import Context, ContextFlag
from .dispatcher import Dispatcher
from . import cache
from .asm.frontend import transpile_file

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


def _wrap_code_object(
    code_obj: types.CodeType,
    lambda_func: types.FunctionType,
    lambdex_ast_node: ast.AST,
    fvmapping: typing.Sequence[int],
) -> types.FunctionType:
    """
    Construct a function using `code_obj`.

    To ensure the two functions have same context, the returned function
    copies `__globals__`, `__defaults__`, and rebuilds `__closure__` from
    `lambda_func`.
    """

    # Trick: Obtain a cell object referencing current function, by
    # constructing a new function and extract its closure.
    callee_ref_cell = (lambda: ret).__closure__[0]

    # Rebuild the closure
    new_closure = tuple(
        lambda_func.__closure__[i] if i >= 0 else callee_ref_cell \
        for i in fvmapping
    )

    ret = types.FunctionType(
        code=code_obj,
        globals=lambda_func.__globals__,
        name=code_obj.co_name,
        argdefs=lambda_func.__defaults__,
        closure=tuple(new_closure),
    )

    if __DEBUG__:
        ret.__ast__ = lambdex_ast_node

    return ret


def _rename_code_object(code, ctx: Context):
    """
    Recursively rename the `co_name` field in all code objects.
    """

    kwargs = {}

    new_name = ctx.renames.get(code.co_name)
    if new_name is not None:
        kwargs['co_name'] = new_name

    new_consts = []
    for const in code.co_consts:
        if inspect.iscode(const):
            const = _rename_code_object(const, ctx)
        new_consts.append(const)
    kwargs['co_consts'] = tuple(new_consts)

    return compat.code_replace(code, **kwargs)


def _resolve_freevars_mapping(
    old_freevars: typing.Sequence[str],
    new_freevars: typing.Sequence[str],
) -> typing.List[int]:
    """
    Return a list `m` such that new_freevars[i] == old_freevars[m[i]].

    m[i] will be -1 if new_freevars[i] not in old_freevars.
    """
    mapping = {v: k for k, v in enumerate(old_freevars)}
    return [mapping.get(varname, -1) for varname in new_freevars]


def _compile(
    ast_node: ast.AST,
    filename: str,
    freevars: typing.Sequence[str],
    globals: typing.Optional[dict] = None,
) -> typing.Tuple[types.CodeType, ast.AST, typing.Sequence[int]]:
    """
    An internal function that do the compilation.
    """
    if globals is None: globals = {}

    context = Context(
        compile_node,
        globals,
        filename,
    )
    lambdex_node = compile_node(
        ast_node,
        ctx=context,
        flag=ContextFlag.outermost_lambdex,
    )

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
            module_code = compile(module_node, filename, 'exec')
        except Exception as e:
            raise SyntaxError(pformat(module_node)) from e
    else:
        module_code = compile(module_node, filename, 'exec')

    # unwrap the outer FunctionDef.
    # since no other definition in the module, it should be co_consts[0]
    wrapper_code = module_code.co_consts[0]

    # the desired code object should be in `module_code.co_consts`
    # we use `.co_name` to identify
    for obj in wrapper_code.co_consts:
        if inspect.iscode(obj) and obj.co_name == lambdex_node.name:
            lambdex_code = obj
            break

    # Append code object name to its co_freevars, so that lambdex
    # can always access itself via its name `anonymous_...`
    callee_name = lambdex_code.co_name
    try:
        callee_index = lambdex_code.co_freevars.index(callee_name)
    except ValueError:
        callee_index = len(lambdex_code.co_freevars)
        lambdex_code = compat.code_replace(
            lambdex_code,
            co_freevars=(*lambdex_code.co_freevars, callee_name),
        )
    freevars_mapping = _resolve_freevars_mapping(freevars, lambdex_code.co_freevars)

    lambdex_code = _rename_code_object(lambdex_code, context)

    return lambdex_code, lambdex_node, freevars_mapping


def compile_lambdex(declarer) -> types.FunctionType:
    """
    Compile a lambda object given by `declarer` into a function.

    Multiple calls with a same declarer yield functions with same code object,
    whilst there closure and globals may be different.
    """
    # If cache hit, simply update metadata and return
    cached_value = cache.get(declarer)
    if cached_value is not None:
        code_obj, lambdex_ast_node, fvmapping = cached_value
        return _wrap_code_object(code_obj, declarer.func, lambdex_ast_node, fvmapping)

    # Otherwise, we have to compile from scratch

    lambda_ast = declarer.get_ast()
    lambda_func = declarer.func

    lambdex_code, lambdex_node, fvmapping = _compile(
        lambda_ast,
        lambda_func.__code__.co_filename,
        lambda_func.__code__.co_freevars,
        lambda_func.__globals__,
    )

    cache.set(declarer, (lambdex_code, lambdex_node, fvmapping))
    transpile_file(lambda_func.__module__)
    return _wrap_code_object(lambdex_code, lambda_func, lambdex_node, fvmapping)
