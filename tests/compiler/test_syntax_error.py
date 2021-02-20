import unittest
import contextlib

from lambdex import def_, async_def_


class TestSyntaxError(unittest.TestCase):

    def _assert_syntax_error(self, factory, msg, lineno, offset):
        with self.assertRaises(SyntaxError) as cm:
            factory()

        exc = cm.exception
        self.assertEqual(exc.msg, msg)
        self.assertEqual(exc.offset, offset)
        lineno = factory.__code__.co_firstlineno + lineno
        self.assertEqual(lineno, exc.lineno)

    def test_lambdex_wrong_body_list(self):
        def factory():
            def_(lambda: ())

        self._assert_syntax_error(factory, "expect '['", 1, 14)

    def test_lambdex_empty_body_list(self):
        def factory():
            def_(lambda: [])

        self._assert_syntax_error(factory, 'empty body', 1, 14)

    def test_nested_lambdex_wrong_body_list(self):
        def factory():
            def_(lambda: [
                def_(lambda: ())
            ])

        self._assert_syntax_error(factory, "expect '['", 2, 30)

    def test_nested_lambdex_empty_body_list(self):
        def factory():
            def_(lambda: [
                def_(lambda: [])
            ])

        self._assert_syntax_error(factory, 'empty body', 2, 30)

    def test_return_multiple_clause(self):
        def factory():
            def_(lambda: [
                return_[a].xxx_[b]
            ])

        self._assert_syntax_error(factory, 'unexpected clause', 2, 31)

    def test_return_with_head(self):
        def factory():
            def_(lambda: [
                return_[a] [b]
            ])

        self._assert_syntax_error(factory, "expect only one group of '[]'", 2, 23)

    def test_if_without_head(self):
        def factory():
            def_(lambda: [
                if_[a]
            ])

        self._assert_syntax_error(factory, "expect another group of '[]'", 2, 19)

    def test_if_multiple_head_items(self):
        def factory():
            def_(lambda: [
                if_[a, b, c][d]
            ])

        self._assert_syntax_error(factory, "expect only one item inside '[]'", 2, 24)

    def test_if_with_wrong_clause(self):
        def factory():
            def_(lambda: [
                if_[a][b].el_[c]
            ])

        self._assert_syntax_error(factory, "expect 'else_' or 'elif_'", 2, 29)

        def factory():
            def_(lambda: [
                if_[a][b].el_[c].else_[d]
            ])

        self._assert_syntax_error(factory, "expect 'elif_'", 2, 29)

    def test_elif_without_head(self):
        def factory():
            def_(lambda: [
                if_[a][b].elif_[c]
            ])

        self._assert_syntax_error(factory, "expect another group of '[]'", 2, 31)

    def test_elif_multiple_head_items(self):
        def factory():
            def_(lambda: [
                if_[a][b].elif_[c, d][e]
            ])

        self._assert_syntax_error(factory, "expect only one item inside '[]'", 2, 36)

    def test_if_else_with_head(self):
        def factory():
            def_(lambda: [
                if_[a][b].else_[c][d]
            ])

        self._assert_syntax_error(factory, "expect only one group of '[]'", 2, 31)

    def test_for_too_many_clauses(self):
        def factory():
            def_(lambda: [
                for_[a][b].else_[c].else_[d]
            ])

        self._assert_syntax_error(factory, 'unexpected clause', 2, 41)

    def test_for_without_head(self):
        def factory():
            def_(lambda: [
                for_[a]
            ])

        self._assert_syntax_error(factory, "expect another group of '[]'", 2, 20)

    def test_for_multiple_head_items(self):
        def factory():
            def_(lambda: [
                for_[a, b][c]
            ])

        self._assert_syntax_error(factory, "expect only one item inside '[]'", 2, 25)

    def test_for_wrong_else_clause(self):
        def factory():
            def_(lambda: [
                for_[a][b].el_[c]
            ])

        self._assert_syntax_error(factory, "expect 'else_'", 2, 30)

    def test_for_else_with_head(self):
        def factory():
            def_(lambda: [
                for_[a][b].else_[c][d]
            ])

        self._assert_syntax_error(factory, "expect only one group of '[]'", 2, 32)

    def test_for_without_in(self):
        def factory():
            def_(lambda: [
                for_[a][b]
            ])

        self._assert_syntax_error(factory, "expect '... in ...'", 2, 22)

    def test_for_too_many_in(self):
        def factory():
            def_(lambda: [
                for_[a in b in c][d]
            ])

        self._assert_syntax_error(factory, 'too many operands', 2, 32)

    def test_for_wrong_in(self):
        def factory():
            def_(lambda: [
                for_[a < b][c]
            ])

        self._assert_syntax_error(factory, "expect 'in' before", 2, 26)

    def test_for_not_lvalue(self):
        def factory():
            def_(lambda: [
                for_[1 in 2][c]
            ])

        self._assert_syntax_error(factory, 'cannot be assigned', 2, 22)

    def test_while_too_many_clauses(self):
        def factory():
            def_(lambda: [
                while_[a][b].else_[c].else_[d]
            ])

        self._assert_syntax_error(factory, 'unexpected clause', 2, 43)

    def test_while_without_head(self):
        def factory():
            def_(lambda: [
                while_[a]
            ])

        self._assert_syntax_error(factory, "expect another group of '[]'", 2, 22)

    def test_while_multiple_head_items(self):
        def factory():
            def_(lambda: [
                while_[a, b][c]
            ])

        self._assert_syntax_error(factory, "expect only one item inside '[]'", 2, 27)

    def test_while_wrong_else_clause(self):
        def factory():
            def_(lambda: [
                while_[a][b].el_[c]
            ])

        self._assert_syntax_error(factory, "expect 'else_'", 2, 32)

    def test_while_else_with_head(self):
        def factory():
            def_(lambda: [
                while_[a][b].else_[c][d]
            ])

        self._assert_syntax_error(factory, "expect only one group of '[]'", 2, 34)

    def test_assignment_not_lvalue(self):
        def factory():
            def_(lambda: [
                a < 1 < 2,
            ])

        self._assert_syntax_error(factory, 'cannot be assigned', 2, 21)

        def factory():
            def_(lambda: [
                (a, 1) < (2, 3),
            ])

        self._assert_syntax_error(factory, 'cannot be assigned', 2, 21)

    def test_with_too_many_clauses(self):
        def factory():
            def_(lambda: [
                with_[a][b].else_[c]
            ])

        self._assert_syntax_error(factory, 'unexpected clause', 2, 33)

    def test_with_without_head(self):
        def factory():
            def_(lambda: [
                with_[a]
            ])

        self._assert_syntax_error(factory, "expect another group of '[]'", 2, 21)

    def test_with_wrong_compare_op(self):
        def factory():
            def_(lambda: [
                with_[a < b][c]
            ])

        self._assert_syntax_error(factory, "expect '>' before", 2, 27)

    def test_with_not_lvalue(self):
        def factory():
            def_(lambda: [
                with_[a > 1][c]
            ])

        self._assert_syntax_error(factory, 'cannot be assigned', 2, 27)

    def test_raise_too_many_clauses(self):
        def factory():
            def_(lambda: [
                raise_[a].b[c].d[e]
            ])

        self._assert_syntax_error(factory, 'unexpected clause', 2, 32)

    def test_raise_with_head(self):
        def factory():
            def_(lambda: [
                raise_[a][b]
            ])

        self._assert_syntax_error(factory, "expect only one group of '[]'", 2, 22)

    def test_raise_with_too_many_items(self):
        def factory():
            def_(lambda: [
                raise_[a, b]
            ])

        self._assert_syntax_error(factory, "expect only one item inside '[]'", 2, 27)

    def test_raise_wrong_from(self):
        def factory():
            def_(lambda: [
                raise_[a].frm_[b]
            ])

        self._assert_syntax_error(factory, "expect 'from_'", 2, 30)


    def test_raise_from_with_head(self):
        def factory():
            def_(lambda: [
                raise_[a].from_[b][c]
            ])

        self._assert_syntax_error(factory, "expect only one group of '[]'", 2, 31)

    def test_raise_with_too_many_items(self):
        def factory():
            def_(lambda: [
                raise_[a].from_[b, c]
            ])

        self._assert_syntax_error(factory, "expect only one item inside '[]'", 2, 36)

    def test_try_bare(self):
        def factory():
            def_(lambda: [
                try_[a]
            ])

        self._assert_syntax_error(factory, "'try_' has neither 'except_' clause(s) nor 'finally_' clause", 2, 20)

    def test_try_wrong_clause(self):
        def factory():
            def_(lambda: [
                try_[a].wrong_[b]
            ])

        self._assert_syntax_error(factory, "unexpected 'wrong_'", 2, 30)

    def test_try_else(self):
        def factory():
            def_(lambda: [
                try_[a].else_[c]
            ])

        self._assert_syntax_error(factory, "unexpected 'else_'", 2, 29)

    def test_try_else_except(self):
        def factory():
            def_(lambda: [
                try_[a].else_[c].except_[b]
            ])

        self._assert_syntax_error(factory, "unexpected 'else_'", 2, 29)

    def test_try_else_finally(self):
        def factory():
            def_(lambda: [
                try_[a].else_[c].finally_[b]
            ])

        self._assert_syntax_error(factory, "unexpected 'else_'", 2, 29)

    def test_try_else_else(self):
        def factory():
            def_(lambda: [
                try_[a].else_[c].else_[b]
            ])

        self._assert_syntax_error(factory, "unexpected 'else_'", 2, 29)

    def test_try_finally_except(self):
        def factory():
            def_(lambda: [
                try_[a].finally_[b].except_[c]
            ])

        self._assert_syntax_error(factory, "unexpected 'except_'", 2, 43)

    def test_try_finally_else(self):
        def factory():
            def_(lambda: [
                try_[a].finally_[b].else_[c]
            ])

        self._assert_syntax_error(factory, "unexpected 'else_'", 2, 41)

    def test_try_finally_finally(self):
        def factory():
            def_(lambda: [
                try_[a].finally_[b].finally_[c]
            ])

        self._assert_syntax_error(factory, "unexpected 'finally_'", 2, 44)

    def test_try_wrong_except(self):
        def factory():
            def_(lambda: [
                try_[a].wrong_[b].except_[c]
            ])

        self._assert_syntax_error(factory, "unexpected 'wrong_'", 2, 30)

    def test_try_defexcept_except(self):
        def factory():
            def_(lambda: [
                try_[a].except_[b].except_[c][d]
            ])

        self._assert_syntax_error(factory, "default 'except_' must be last", 2, 31)

    def test_try_except_wrong_op(self):
        def factory():
            def_(lambda: [
                try_[a].except_[b < c][d]
            ])

        self._assert_syntax_error(factory, "expect '>' before", 2, 37)

    def test_try_except_too_many_operands(self):
        def factory():
            def_(lambda: [
                try_[a].except_[b > c > d][e]
            ])

        self._assert_syntax_error(factory, 'too many operands', 2, 41)


    def test_try_except_not_identifier(self):
        def factory():
            def_(lambda: [
                try_[a].except_[b > 1][e]
            ])

        self._assert_syntax_error(factory, 'expect identifier', 2, 37)

        def factory():
            def_(lambda: [
                try_[a].except_[b > c[d]][e]
            ])

        self._assert_syntax_error(factory, 'expect identifier', 2, 37)

    def test_try_else_with_head(self):
        def factory():
            def_(lambda: [
                try_[a].except_[b].else_[c][d]
            ])

        self._assert_syntax_error(factory, "expect only one group of '[]'", 2, 40)

    def test_try_finally_with_head(self):
        def factory():
            def_(lambda: [
                try_[a].finally_[b][c]
            ])

        self._assert_syntax_error(factory, "expect only one group of '[]'", 2, 32)

    def test_yield_too_many_clauses(self):
        def factory():
            def_(lambda: [
                yield_[a].wrong_[b]
            ])

        self._assert_syntax_error(factory, 'unexpected clause', 2, 32)

    def test_yield_with_head(self):
        def factory():
            def_(lambda: [
                yield_[a][b]
            ])

        self._assert_syntax_error(factory, "expect only one group of '[]'", 2, 22)

    def test_yield_from_too_many_clauses(self):
        def factory():
            def_(lambda: [
                yield_from_[a].wrong_[b]
            ])

        self._assert_syntax_error(factory, 'unexpected clause', 2, 37)

    def test_yield_from_with_head(self):
        def factory():
            def_(lambda: [
                yield_from_[a][b]
            ])

        self._assert_syntax_error(factory, "expect only one group of '[]'", 2, 27)

    def test_global_too_many_clauses(self):
        def factory():
            def_(lambda: [
                global_[a].wrong_[b]
            ])

        self._assert_syntax_error(factory, 'unexpected clause', 2, 33)

    def test_global_with_head(self):
        def factory():
            def_(lambda: [
                global_[a][b]
            ])

        self._assert_syntax_error(factory, "expect only one group of '[]'", 2, 23)

    def test_global_not_name_1(self):
        def factory():
            def_(lambda: [
                global_[a, 1]
            ])

        self._assert_syntax_error(factory, 'expect identifier', 2, 28)

    def test_global_not_name_2(self):
        def factory():
            def_(lambda: [
                global_[a, b[c]]
            ])

        self._assert_syntax_error(factory, 'expect identifier', 2, 28)

    def test_nonlocal_too_many_clauses(self):
        def factory():
            def_(lambda: [
                nonlocal_[a].wrong_[b]
            ])

        self._assert_syntax_error(factory, 'unexpected clause', 2, 35)

    def test_nonlocal_with_head(self):
        def factory():
            def_(lambda: [
                nonlocal_[a][b]
            ])

        self._assert_syntax_error(factory, "expect only one group of '[]'", 2, 25)

    def test_nonlocal_not_name_1(self):
        def factory():
            def_(lambda: [
                nonlocal_[a, 1]
            ])

        self._assert_syntax_error(factory, 'expect identifier', 2, 30)

    def test_nonlocal_not_name_2(self):
        def factory():
            def_(lambda: [
                nonlocal_[a, b[c]]
            ])

        self._assert_syntax_error(factory, 'expect identifier', 2, 30)

    def test_del_too_many_clauses(self):
        def factory():
            def_(lambda: [
                del_[a].wrong_[b]
            ])

        self._assert_syntax_error(factory, 'unexpected clause', 2, 30)

    def test_del_with_head(self):
        def factory():
            def_(lambda: [
                del_[a][b]
            ])

        self._assert_syntax_error(factory, "expect only one group of '[]'", 2, 20)

    def test_del_not_lvalue_1(self):
        def factory():
            def_(lambda: [
                del_[a, 1]
            ])

        self._assert_syntax_error(factory, 'cannot be deleted', 2, 25)

    def test_del_not_lvalue_2(self):
        def factory():
            def_(lambda: [
                del_[a, b(), []]
            ])

        self._assert_syntax_error(factory, 'cannot be deleted', 2, 25)

    def test_return_too_many_clauses(self):
        def factory():
            def_(lambda: [
                return_[a].b[c]
            ])

        self._assert_syntax_error(factory, 'unexpected clause', 2, 28)

    def test_return_with_head(self):
        def factory():
            def_(lambda: [
                return_[a][b]
            ])

        self._assert_syntax_error(factory, "expect only one group of '[]'", 2, 23)

    def test_slice_in_brackets(self):
        def factory():
            def_(lambda: [
                return_[:]
            ])

        self._assert_syntax_error(factory, "':' is not allowed in '[]'", 2, 23)

        def factory():
            def_(lambda: [
                return_[:, :]
            ])

        self._assert_syntax_error(factory, "':' is not allowed in '[]'", 2, 23)

    def test_async_for_in_normal_func(self):
        def factory():
            def_(lambda: [
                async_for_[a in b] [
                    pass_
                ]
            ])

        self._assert_syntax_error(factory, "'async_for_' outside async function", 2, 26)

    def test_async_for_in_nested_normal_func(self):
        def factory():
            async_def_(lambda: [
                def_(lambda: [
                    async_for_[a][b]
                ])
            ])

        self._assert_syntax_error(factory, "'async_for_' outside async function", 3, 30)

    def test_async_with_in_normal_func(self):
        def factory():
            def_(lambda: [
                async_with_[a in b] [
                    pass_
                ]
            ])

        self._assert_syntax_error(factory, "'async_with_' outside async function", 2, 27)

    def test_async_with_in_nested_normal_func(self):
        def factory():
            async_def_(lambda: [
                def_(lambda: [
                    async_with_[a][b]
                ])
            ])

        self._assert_syntax_error(factory, "'async_with_' outside async function", 3, 31)

    def test_await_in_normal_func(self):
        def factory():
            def_(lambda: [
                await_[a]
            ])

        self._assert_syntax_error(factory, "'await_' outside async function", 2, 22)

    def test_await_in_nested_normal_func(self):
        def factory():
            async_def_(lambda: [
                def_(lambda: [
                    await_[a]
                ])
            ])

        self._assert_syntax_error(factory, "'await_' outside async function", 3, 26)

    def test_await_too_many_clauses(self):
        def factory():
            async_def_(lambda: [
                await_[a].b[c].d[e]
            ])

        self._assert_syntax_error(factory, 'unexpected clause', 2, 32)

    def test_await_with_head(self):
        def factory():
            async_def_(lambda: [
                await_[a][b]
            ])

        self._assert_syntax_error(factory, "expect only one group of '[]'", 2, 22)

    def test_await_with_too_many_items(self):
        def factory():
            async_def_(lambda: [
                await_[a, b]
            ])

        self._assert_syntax_error(factory, "expect only one item inside '[]'", 2, 27)

