import sys
import enum
import types

if sys.version_info < (3, 8):
    _code_fields = ['argcount', 'kwonlyargcount', 'nlocals', 'stacksize', 'flags', 'codestring',
        'consts', 'names', 'varnames', 'filename', 'name', 'firstlineno', 'lnotab', 'freevars',
        'cellvars']

    _code_a2f = {n: 'co_' + n for n in _code_fields}
    _code_a2f['codestring'] = 'co_code'
    _code_f2a = {v: k for k, v in _code_a2f.items()}

    def code_replace(code_obj, **kwargs):
        arguments = {}
        for field in _code_fields:
            arguments[field] = getattr(code_obj, _code_a2f[field])

        for key, value in kwargs.items():
            assert key.startswith('co_')
            arguments[_code_f2a[key]] = value

        arguments = [arguments[n] for n in _code_fields]

        return types.CodeType(*arguments)

else:
    code_replace = types.CodeType.replace

if sys.version_info < (3, 6):

    def enum_auto():
        _counter = 0

        def _auto():
            nonlocal _counter
            _counter += 1
            return _counter

        return _auto

else:

    def enum_auto():
        return enum.auto