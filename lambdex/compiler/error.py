import ast
import linecache


def assert_(cond: bool, msg: str, node: ast.AST, filename: str):
    if cond:
        return

    if callable(node): node = node()

    if isinstance(node, (ast.Attribute, ast.Name)):
        lineno = node.end_lineno
        offset = node.end_col_offset
    else:
        lineno = node.lineno
        offset = node.col_offset + 1

    raise SyntaxError(msg, (
        filename,
        lineno,
        offset,
        linecache.getline(filename, lineno),
    ))
