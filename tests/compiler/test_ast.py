import unittest

from astcheck import assert_ast_like

from lambdex.keywords import *
from lambdex.compiler import core
from lambdex.utils.ast import ast_from_source, pformat, pprint, recursively_set_attr, is_coroutine_ast


class TestAST(unittest.TestCase):
    def setUp(self):
        core.__DEBUG__ = True

    def tearDown(self):
        core.__DEBUG__ = False

    def assert_ast_like(self, f, target):
        ast_f = f.__ast__
        recursively_set_attr(ast_f, 'type_comment', None)
        if is_coroutine_ast(ast_f):
            keyword = 'async def'
        else:
            keyword = 'def'
        ast_target = ast_from_source(target, keyword)
        ast_target.name = ast_f.name

        try:
            assert_ast_like(ast_f, ast_target)
        except AssertionError as cause:
            msg = '\n'.join(['', '===> Compiled:', pformat(ast_f), '===> Target:', pformat(ast_target)])
            raise AssertionError(msg) from cause

    def test_return_single_value(self):
        f = def_(lambda: [
            return_[x],
        ])

        def target():
            return x

        self.assert_ast_like(f, target)

    def test_return_tuple_without_parentheses(self):
        f = def_(lambda: [
            return_[x, y],
        ])

        def target():
            return x, y

        self.assert_ast_like(f, target)

    def test_return_tuple_with_parentheses(self):
        f = def_(lambda: [
            return_[(x, y)],
        ])

        def target():
            return x, y

        self.assert_ast_like(f, target)

    def test_return_body_compiled(self):
        f = def_(lambda: [
            return_[yield_, yield_],
        ])

        def target():
            return ((yield), (yield))

        self.assert_ast_like(f, target)

    def test_pass(self):
        f = def_(lambda: [
            pass_,
        ])

        def target():
            pass

        self.assert_ast_like(f, target)

    def test_if(self):
        f = def_(lambda: [
            if_[a] [
                b, 
            ],
        ])

        def target():
            if a:
                b

        self.assert_ast_like(f, target)

    def test_if_elif(self):
        f = def_(lambda: [
            if_[a] [
                b, 
            ].elif_[c] [
                d, 
            ],
        ])

        def target():
            if a:
                b
            elif c:
                d

        self.assert_ast_like(f, target)

    def test_if_elif_multiple(self):
        f = def_(lambda: [
            if_[a] [
                b, 
            ].elif_[c] [
                d, 
            ].elif_[c] [
                d, 
            ],
        ])

        def target():
            if a:
                b
            elif c:
                d
            elif c:
                d

        self.assert_ast_like(f, target)

    def test_if_else(self):
        f = def_(lambda: [
            if_[a] [
                b, 
            ].else_ [
                d,
            ],
        ])

        def target():
            if a:
                b
            else:
                d

        self.assert_ast_like(f, target)

    def test_if_elif_else(self):
        f = def_(lambda: [
            if_[a] [
                b, 
            ].elif_[c] [
                d, 
            ].else_ [
                d,
            ],
        ])

        def target():
            if a:
                b
            elif c:
                d
            else:
                d

        self.assert_ast_like(f, target)

    def test_if_body_compiled(self):
        f = def_(lambda: [
            if_[a] [
                a < 1, 
            ].else_ [
                d,
            ],
        ])

        def target():
            if a:
                a = 1
            else:
                d

        self.assert_ast_like(f, target)

    def test_if_elif_body_compiled(self):
        f = def_(lambda: [
            if_[a] [
                b, 
            ].elif_[c] [
                a < 1, 
            ].else_ [
                d,
            ],
        ])

        def target():
            if a:
                b
            elif c:
                a = 1
            else:
                d

        self.assert_ast_like(f, target)

    def test_if_else_body_compiled(self):
        f = def_(lambda: [
            if_[a] [
                b, 
            ].else_ [
                a < 1,
            ],
        ])

        def target():
            if a:
                b
            else:
                a = 1

        self.assert_ast_like(f, target)

    def test_if_head_compiled(self):
        f = def_(lambda: [
            if_[yield_] [
                b, 
            ],
        ])

        def target():
            if (yield):
                b

        self.assert_ast_like(f, target)

    def test_if_elif_head_compiled(self):
        f = def_(lambda: [
            if_[a] [
                b, 
            ].elif_[yield_] [
                b, 
            ],
        ])

        def target():
            if a:
                b
            elif (yield):
                b

        self.assert_ast_like(f, target)

    def test_for(self):
        f = def_(lambda: [
            for_[a in b] [
                c, 
            ],
        ])

        def target():
            for a in b:
                c

        self.assert_ast_like(f, target)

    def test_for_else(self):
        f = def_(lambda: [
            for_[a in b] [
                c, 
            ].else_ [
                d,
            ],
        ])

        def target():
            for a in b:
                c
            else:
                d

        self.assert_ast_like(f, target)

    def test_for_body_compiled(self):
        f = def_(lambda: [
            for_[a in b] [
                a < 1, 
            ],
        ])

        def target():
            for a in b:
                a = 1

        self.assert_ast_like(f, target)

    def test_for_else_body_compiled(self):
        f = def_(lambda: [
            for_[a in b] [
                c, 
            ].else_ [
                a < 1,
            ],
        ])

        def target():
            for a in b:
                c
            else:
                a = 1

        self.assert_ast_like(f, target)

    def test_for_iter_compiled(self):
        f = def_(lambda: [
            for_[a in (yield_)] [
                b, 
            ],
        ])

        def target():
            for a in (yield):
                b

        self.assert_ast_like(f, target)

    def test_while(self):
        f = def_(lambda: [
            while_[a] [
                b, 
            ],
        ])

        def target():
            while a:
                b

        self.assert_ast_like(f, target)

    def test_while_else(self):
        f = def_(lambda: [
            while_[a] [
                b, 
            ].else_ [
                c,
            ],
        ])

        def target():
            while a:
                b
            else:
                c

        self.assert_ast_like(f, target)

    def test_while_body_compiled(self):
        f = def_(lambda: [
            while_[a] [
                a < 1, 
            ],
        ])

        def target():
            while a:
                a = 1

        self.assert_ast_like(f, target)

    def test_while_else_body_compiled(self):
        f = def_(lambda: [
            while_[a] [
                b, 
            ].else_ [
                a < 1,
            ],
        ])

        def target():
            while a:
                b
            else:
                a = 1

        self.assert_ast_like(f, target)

    def test_while_head_compiled(self):
        f = def_(lambda: [
            while_[yield_] [
                b, 
            ],
        ])

        def target():
            while (yield):
                b

        self.assert_ast_like(f, target)

    def test_break(self):
        f = def_(lambda: [
            while_[a] [
                break_, 
            ],
        ])

        def target():
            while a:
                break

        self.assert_ast_like(f, target)

    def test_continue(self):
        f = def_(lambda: [
            while_[a] [
                continue_, 
            ],
        ])

        def target():
            while a:
                continue

        self.assert_ast_like(f, target)

    def test_assignment(self):
        f = def_(lambda: [
            a < 1,
        ])

        def target():
            a = 1

        self.assert_ast_like(f, target)

    def test_assignment_other_compare(self):
        f = def_(lambda: [
            a <= b <= c
        ])

        def target():
            a <= b <= c

        self.assert_ast_like(f, target)

    def test_assignment_chained(self):
        f = def_(lambda: [
            a < b[c] < d < 1,
        ])

        def target():
            a = b[c] = d = 1

        self.assert_ast_like(f, target)

    def test_assignment_destruct(self):
        f = def_(lambda: [
            (a, *b, c) < (d, e) < [f, g] < 1,
        ])

        def target():
            (a, *b, c) = (d, e) = [f, g] = 1

        self.assert_ast_like(f, target)

    def test_assignment_op_in_other_context(self):
        f = def_(lambda: [
            a < 1,
            while_[a < 1] [
                pass_, 
            ],
        ])

        def target():
            a = 1
            while a < 1:
                pass

        self.assert_ast_like(f, target)

    def test_assignment_value_compiled(self):
        f = def_(lambda: [
            a < yield_,
        ])

        def target():
            a = yield

        self.assert_ast_like(f, target)

    def test_with(self):
        f = def_(lambda: [
            with_[a] [
                b, 
            ],
        ])

        def target():
            with a:
                b

        self.assert_ast_like(f, target)

    def test_with_as(self):
        f = def_(lambda: [
            with_[a > b] [
                c, 
            ],
        ])

        def target():
            with a as b:
                c

        self.assert_ast_like(f, target)

    def test_with_as_multiple(self):
        f = def_(lambda: [
            with_[a > b.c, d > e[f]] [
                g, 
            ],
        ])

        def target():
            with a as b.c, d as e[f]:
                g

        self.assert_ast_like(f, target)

    def test_with_body_compiled(self):
        f = def_(lambda: [
            with_[a] [
                b < c, 
            ],
        ])

        def target():
            with a:
                b = c

        self.assert_ast_like(f, target)

    def test_with_value_compiled(self):
        f = def_(lambda: [
            with_[yield_] [
                b, 
            ],
        ])

        def target():
            with (yield):
                b

        self.assert_ast_like(f, target)

    def test_raise(self):
        f = def_(lambda: [
            raise_[a],
        ])

        def target():
            raise a

        self.assert_ast_like(f, target)

    def test_raise_bare(self):
        f = def_(lambda: [
            try_ [
                ...
            ].except_ [
                raise_
            ]
        ])

        def target():
            try:
                ...
            except:
                raise

        self.assert_ast_like(f, target)

    def test_raise_from(self):
        f = def_(lambda: [
            raise_[a].from_[b],
        ])

        def target():
            raise a from b

        self.assert_ast_like(f, target)

    def test_raise_value_compiled(self):
        f = def_(lambda: [
            raise_[yield_],
        ])

        def target():
            raise (yield)

        self.assert_ast_like(f, target)

    def test_raise_cause_compiled(self):
        f = def_(lambda: [
            raise_[e].from_[yield_],
        ])

        def target():
            raise e from (yield)

        self.assert_ast_like(f, target)

    def test_try_except(self):
        f = def_(lambda: [
            try_ [
                a,
            ].except_ [
                b,
            ],
        ])

        def target():
            try:
                a
            except:
                b

        self.assert_ast_like(f, target)

    def test_try_except_exc(self):
        f = def_(lambda: [
            try_ [
                a,
            ].except_[exc] [
                b, 
            ],
        ])

        def target():
            try:
                a
            except exc:
                b

        self.assert_ast_like(f, target)

    def test_try_except_e_as(self):
        f = def_(lambda: [
            try_ [
                a,
            ].except_[exc > e] [
                b, 
            ],
        ])

        def target():
            try:
                a
            except exc as e:
                b

        self.assert_ast_like(f, target)

    def test_try_except_multiple(self):
        f = def_(lambda: [
            try_ [
                a,
            ].except_[exc > e] [
                b, 
            ].except_[exc2 > e] [
                b, 
            ],
        ])

        def target():
            try:
                a
            except exc as e:
                b
            except exc2 as e:
                b

        self.assert_ast_like(f, target)

    def test_try_except_else(self):
        f = def_(lambda: [
            try_ [
                a,
            ].except_[exc > e] [
                b, 
            ].else_ [
                b,
            ],
        ])

        def target():
            try:
                a
            except exc as e:
                b
            else:
                b

        self.assert_ast_like(f, target)

    def test_try_except_finally(self):
        f = def_(lambda: [
            try_ [
                a,
            ].except_[exc > e] [
                b, 
            ].finally_ [
                b,
            ],
        ])

        def target():
            try:
                a
            except exc as e:
                b
            finally:
                b

        self.assert_ast_like(f, target)

    def test_try_except_else_finally(self):
        f = def_(lambda: [
            try_ [
                a,
            ].except_[exc > e] [
                b, 
            ].else_ [
                b,
            ].finally_ [
                b,
            ],
        ])

        def target():
            try:
                a
            except exc as e:
                b
            else:
                b
            finally:
                b

        self.assert_ast_like(f, target)

    def test_try_finally(self):
        f = def_(lambda: [
            try_ [
                a,
            ].finally_ [
                b,
            ],
        ])

        def target():
            try:
                a
            finally:
                b

        self.assert_ast_like(f, target)

    def test_try_body_compiled(self):
        f = def_(lambda: [
            try_ [
                a < 1,
            ].except_ [
                b,
            ],
        ])

        def target():
            try:
                a = 1
            except:
                b

        self.assert_ast_like(f, target)

    def test_try_except_body_compiled(self):
        f = def_(lambda: [
            try_ [
                a,
            ].except_ [
                a < 1,
            ],
        ])

        def target():
            try:
                a
            except:
                a = 1

        self.assert_ast_like(f, target)

    def test_try_else_body_compiled(self):
        f = def_(lambda: [
            try_ [
                a,
            ].except_ [
                b,
            ].else_ [
                a < 1,
            ],
        ])

        def target():
            try:
                a
            except:
                b
            else:
                a = 1

        self.assert_ast_like(f, target)

    def test_try_finally_body_compiled(self):
        f = def_(lambda: [
            try_ [
                a,
            ].finally_ [
                a < 1,
            ],
        ])

        def target():
            try:
                a
            finally:
                a = 1

        self.assert_ast_like(f, target)

    def test_try_except_head_compiled(self):
        f = def_(lambda: [
            try_ [
                a,
            ].except_[yield_ > e] [
                a, 
            ],
        ])

        def target():
            try:
                a
            except (yield) as e:
                a

        self.assert_ast_like(f, target)

    def test_yield(self):
        f = def_(lambda: [
            yield_,
        ])

        def target():
            yield

        self.assert_ast_like(f, target)

    def test_yield_single_value(self):
        f = def_(lambda: [
            yield_[a],
        ])

        def target():
            yield a

        self.assert_ast_like(f, target)

    def test_yield_tuple(self):
        f = def_(lambda: [
            yield_[a, b],
            yield_[(a, b)],
        ])

        def target():
            yield a, b
            yield a, b

        self.assert_ast_like(f, target)

    def test_yield_value_compiled(self):
        f = def_(lambda: [
            yield_[yield_],
        ])

        def target():
            yield (yield)

        self.assert_ast_like(f, target)

    def test_yield_from(self):
        f = def_(lambda: [
            yield_from_[a],
        ])

        def target():
            yield from a

        self.assert_ast_like(f, target)

    def test_yield_from_tuple(self):
        f = def_(lambda: [
            yield_from_[a, b],
        ])

        def target():
            yield from (a, b)

        self.assert_ast_like(f, target)

    def test_yield_from_value_compiled(self):
        f = def_(lambda: [
            yield_from_[yield_],
        ])

        def target():
            yield from (yield)

        self.assert_ast_like(f, target)

    def test_nonlocal(self):
        a = 1

        f = def_(lambda: [
            nonlocal_[a],
        ])

        def target():
            nonlocal a

        self.assert_ast_like(f, target)

    def test_global(self):
        f = def_(lambda: [
            global_[a],
        ])

        def target():
            global a

        self.assert_ast_like(f, target)

    def test_del(self):
        a = 1

        f = def_(lambda: [
            del_[a, b[c]],
        ])

        def target():
            del a, b[c]

        self.assert_ast_like(f, target)

    def test_simple_lambda(self):
        f = def_(lambda: [
            lambda: [return_[1]]
        ])

        def target():
            lambda: [return_[1]]

        self.assert_ast_like(f, target)

    def test_callee(self):
        f = def_(lambda: [
            return_[callee_],
        ])

        self.assertIs(f, f())

    def test_inner_callee(self):
        f = def_(lambda: [
            inner < def_(lambda: [
                return_[callee_]
            ]),
            inner_callee < inner(),
            return_[inner, inner_callee, callee_],
        ])

        fi, fic, c = f()
        self.assertIs(fi, fic)
        self.assertIs(f, c)

    def test_async_def(self):
        f = async_def_(lambda: [
            a < 1
        ])

        async def target():
            a = 1

        self.assert_ast_like(f, target)

    def test_async_for(self):
        f = async_def_(lambda: [
            async_for_[i in range(10)] [
                pass_
            ]
        ])

        async def target():
            async for i in range(10):
                pass

        self.assert_ast_like(f, target)

    def test_async_with(self):
        f = async_def_(lambda: [
            async_with_[a > b] [
                pass_
            ]
        ])

        async def target():
            async with a as b:
                pass

        self.assert_ast_like(f, target)

    def test_await(self):
        f = async_def_(lambda: [
            await_[a]
        ])

        async def target():
            await a

        self.assert_ast_like(f, target)

    def test_arg_default(self):
        b = lambda: ()
        f = def_(lambda a=b(): [
            return_[a]
        ])

        def target(a=b()):
            return a

        self.assert_ast_like(f, target)

    def test_kwarg_default(self):
        b = lambda: ()
        f = def_(lambda *, a=b(): [
            return_[a]
        ])

        def target(*, a=b()):
            return a

        self.assert_ast_like(f, target)
