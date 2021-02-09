from lambdex.fmt.core.definitions import tk, A, TokenInfo, actions
from lambdex.fmt.core._stream_base import _StreamWithLog

REPLACE = 1
INSERT = 2


class Scope:

    __slots__ = ['leading_whitespace', 'indent_level']

    def __init__(self, leading_whitespace, *, indent_level=0):
        self.leading_whitespace = leading_whitespace
        self.indent_level = indent_level


class Reindent(_StreamWithLog):

    SPACES_PER_TAB = 4

    def _init(self):
        self.indent_initialized = False
        self.orig_indent_str = '    '
        self.spaced_indent_str = '    '

        self.str_newline = None

        self.newlined = False
        self.last_leading_whitespace = ''
        self.scopes = []

    def _to_spaced(self, string: str) -> str:
        return string.replace('\t', ' ' * self.SPACES_PER_TAB)

    def _restore_tabbed(self, string: str) -> str:
        return string.replace(self.spaced_indent_str, self.orig_indent_str)

    def _store_constant(self, token: TokenInfo):
        if token.type == tk.INDENT and not self.indent_initialized:
            self.indent_initialized = True
            self.orig_indent_str = token.string
            self.spaced_indent_str = self._to_spaced(token.string)
        elif token.is_NL and self.str_newline is None:
            self.str_newline = token.string

    def _process_leading_whitespace(self, token: TokenInfo):
        if not self.scopes:
            if token.is_WS_NL or token.type == tk.INDENT:
                return token, REPLACE
            else:
                return TokenInfo(type=tk.WHITESPACE, string=''), INSERT

        if token.is_WS:
            orig_lws = token.string
            action = REPLACE
        elif not token.is_NL:
            orig_lws = ''
            action = INSERT
        else:
            return token, REPLACE

        indentation = self.spaced_indent_str * self.scopes[-1].indent_level + self.scopes[-1].leading_whitespace
        orig_lws = self._to_spaced(orig_lws)

        if token.leading_whitespace is not None:
            orig_parent_lws = self._to_spaced(token.leading_whitespace)
            if orig_lws.startswith(orig_parent_lws):
                indentation += orig_lws[len(orig_parent_lws):]
            else:
                indentation = indentation[:len(orig_lws) - len(orig_parent_lws)]

        indentation = self._restore_tabbed(indentation)

        return TokenInfo(type=tk.WHITESPACE, string=indentation), action

    def _handle_token(self, token):
        if token.type == tk.ENCODING: return
        self._store_constant(token)

        if self.newlined:
            new_whitespace, action = self._process_leading_whitespace(token)
            if action == REPLACE:
                token = new_whitespace
            elif action == INSERT:
                yield new_whitespace

            self.last_leading_whitespace = new_whitespace.string
            self.newlined = False

        if token.annotation == A.DECL_LPAR:
            self.scopes.append(Scope(self.last_leading_whitespace))
        elif token.annotation == A.DECL_RPAR:
            self.scopes.pop()

        if token.annotation in (A.BODY_LSQB, A.CLS_BODY_LSQB):
            self.scopes[-1].indent_level += 1

        if token.annotation in (A.LAST_NL_BEFORE_RSQB, ):
            self.scopes[-1].indent_level -= 1

        if token.is_NL:
            self.newlined = True

        yield token
        self.action = actions.Default(dont_store=True)
