import libcst.matchers as m

__all__ = [
    'M_LAMBDEX',
    'M_CLAUSE',
    'matches',
]

M_LAMBDEX = m.Call(
    func=(m.Name('def_') | m.Attribute(value=m.Name('def_'))),
    args=[m.Arg(m.Lambda())],
)

M_CLAUSE = \
    (m.Subscript(
        value=m.Subscript(
            value=(
                m.Name(m.MatchRegex(r'if_|for_|while_|with_'))
                | m.Attribute(attr=m.Name(m.MatchRegex(r'elif_|except_')))
            )
        )
    ) | m.Subscript(
        value=(
            m.Name(m.MatchRegex(r'try_'))
            | m.Attribute(attr=m.Name(m.MatchRegex(r'except_|finally_|else_')))
        )
    ))

matches = m.matches