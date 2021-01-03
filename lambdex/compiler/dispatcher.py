import ast

from lambdex.utils.registry import FunctionRegistry

__all__ = ['Dispatcher']

Dispatcher = FunctionRegistry('Dispatcher').set_default(lambda *_: None)


@Dispatcher.register(ast.Call)
def disp_Call(node: ast.Call):
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
def disp_Subscript(node: ast.Subscript):
    value = node.value

    if not isinstance(value, ast.Name):
        return None

    return {
        'return_': ast.Return,
    }.get(value.id)