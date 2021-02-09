# v0.4.0

## What's New

**lambdex** is now supporting keyword and operator customization! See the [docs](../docs/Customization.md) for more details.

## BugFix

### Formatter

- `lambdex.fmt` should ensure NEWLINE at the end when writing to stdout. ([3cbc0fc](../../commit/3cbc0fceca803aa9fb5e227274d47b2c40ab0a7a))

### CI

- Fix missing target `test_repl_ipython`. ([bb7e9d2](../../commit/bb7e9d205bfa7722b00a7427947b7159c2ed04c6))

# v0.3.0

## What's New

**lambdex** is now able to run in REPL! Currently three environments **built-in Python REPL**, **IDLE** and **IPython (Jupyter)** are supported.

## BugFix

### Compiler

- Top-level script checking in `lambdex/__init__.py` should check the first frame that contains no `'importlib'`. ([6e1dfb8](../../commit/6e1dfb86ab77f5160bcc4d9fe9b5c2eeef862e8e))
- Top-level script checking in `lambdex/__init__.py` should not fail if `site.getusersitepackages` not available. ([f174187](../../commit/f174187cccf4614d8a4afc4bcc328145c1bb4ded))
- `lambdex.utils.ast::ast_from_source` should not assume that lines are ending with line separators. ([e6aa950](../../commit/e6aa9507abdade2479167abc1dec1c7cb5b4dbe5))

# v0.2.0

## What's New

- Support and tested on Python 3.5, 3.6, 3.7, 3.8, 3.9, 3.10-dev.
- Improve the compile-time error messages.

## BugFix

### Compiler

- Use `sys` instead of `inspect` to check current running environment (as executable or module) in `lambdex/__init__.py`. `inspect` has far more dependencies than `sys`, which may cause module name conflicts in **lxfmt**. ([8a43346](../../commit/8a43346c087db4f6eb1bc158e6a5554dfce640a1))
- `lambdex.utils.ast::is_lvalue` should check recursively. L-value checking is also removed in `lambdex.utils.ast::cast_to_lvalue`. ([55fbfb6](../../commit/55fbfb6351778db9f41ea04cec9e7b6be3ec115c), [8c801bd](../../commit/8c801bd1bb65b1611c3847e101088c88288bf6cd))
- `lambdex.utils.ast::check_compare` should ensure that argument `node` is of type `ast.Compare`. ([5fbe3d5](../../commit/5fbe3d52b3dd93dc4e5e6754ebcb365b8015eda7))
- Comparisons other than assignments should not raise a `SyntaxError` in body. This allows expressions like `a > b` to exist in body. ([73c228d](../../commit/73c228d7e252a11562684032a31bf1326452eb34))
- Default `except_` should be the last exception handler. Otherwise a `SyntaxError` raised. ([9091565](../../commit/9091565b688cd9af550db83cee45f82c1c965ee1))
- Should raise a `SyntaxError` when `finally_` has a clause head. ([ee70df0](../../commit/ee70df030e9a07304821b31b0fcb9fa0ddb681be))
- Should raise a `SyntaxError` when unknown clause encountered in a `try_` block. ([16edff4](../../commit/16edff4b2b70b47452e369e31cf5f0127d7b9009))
- Should raise a `SyntaxError` when `Slice` node found in `ExtSlice` node. This disallows code like `if_[a:b][...]`. ([77d796f](../../commit/77d796fb1e2a952deba18532fd760f36704e4d49))

# v0.1.0

## What's New

### Compiler

- Add detailed compile-time and runtime error messages.

# v0.0.1

## What's New

### Syntax Features

- `<` assignments
- `if_`, `elif_`, `else_`
- `for_`, `else_`
- `while_`, `else_`
- `try_`, `except_`, `else_`, `finally_`
- `with_`
- `nonlocal_`, `global_`
- `pass_`
- `return_`
- `raise_`, `from_`
- `yield_`, `yield_from_`
- Nested lambdex

### Compiler

- Bytecode caching

### Formatter

- CLI tool `lxfmt`
- CLI tool `lxfmt-mock`
