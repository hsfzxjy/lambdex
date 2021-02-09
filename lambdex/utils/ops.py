import ast

# Mapping from operator string to AST node type
COMPARATORS = {
    '<': ast.Lt,
    '<=': ast.LtE,
    '>': ast.Gt,
    '>=': ast.GtE,
    'in': ast.In,
}

COMPARATORS_S2A = {v: k for k, v in COMPARATORS.items()}
