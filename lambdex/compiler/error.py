import sys
import ast
import linecache

if sys.version_info < (3, 8):
    import re
    from os import linesep

    def _get_end_lineinfo(node: ast.AST, filename: str):
        """
        Fallback function to get endling lineno and col_offset of `node`.
        """
        def _get_last_child_loc():
            """
            Return the lineinfo for child of `node` with maximum lineno and col_offset.
            """
            last_child_loc = None
            for n in ast.walk(node):
                if n is node: continue

                if isinstance(n, (ast.Name, ast.Attribute)):
                    # If n is Name or Attribute, use its ending location
                    loc = _get_end_lineinfo(n, filename)
                elif 'lineno' in n._fields:
                    # Otherwise, use its starting location
                    loc = (n.lineno, n.col_offset)
                else:
                    # If no attribute `lineno`, simply ignore it
                    continue

                if not last_child_loc or last_child_loc < loc:
                    last_child_loc = loc

            return last_child_loc

        if isinstance(node, ast.Name):
            return (node.lineno, node.col_offset + len(node.id))
        elif isinstance(node, ast.Attribute):
            regexp = re.compile(r'''
                \.               # a single dot
                (                # following with arbitary whitespaces / comments:
                    \s*          #      zero or more leading whitespaces
                    (            #      zero or one ending tokens
                        \\       #          CONTINUE
                        |\#.*    #          COMMENT
                    )?           #
                    \n+          #      one or more newlines
                )*               #
                \s*              # zero or more whitespaces
                {}               # the target attribute name
            '''.format(node.attr), re.MULTILINE | re.VERBOSE)
            lines = linecache.getlines(filename)
            lineno, col_offset = _get_last_child_loc()
            text_after = lines[lineno - 1][col_offset:] + ''.join(lines[lineno:])
            text_after = text_after.replace(linesep, '\n')
            matched = re.search(regexp, text_after)
            matched_lines = text_after[:matched.end()].split('\n')
            if len(matched_lines) == 1:
                # On the same line
                return lineno, col_offset + matched.end()
            else:
                # On different line
                return lineno + len(matched_lines) - 1, len(matched_lines[-1])
        else:
            raise RuntimeError
else:

    def _get_end_lineinfo(node: ast.AST, filename: str):
        return node.end_lineno, node.end_col_offset


def assert_(cond: bool, msg: str, node: ast.AST, filename: str):
    if cond:
        return

    if callable(node): node = node()

    if isinstance(node, (ast.Attribute, ast.Name)):
        lineno, offset = _get_end_lineinfo(node, filename)
    else:
        lineno = node.lineno
        offset = node.col_offset + 1

    raise SyntaxError(msg, (
        filename,
        lineno,
        offset,
        linecache.getline(filename, lineno),
    ))
