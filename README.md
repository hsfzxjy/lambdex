<h1 style="text-align: center">lambdex</h1>

**lambdex** allows you to write multi-line anonymous function expression (called a _lambdex_) in an idiomatic manner. Below is a quick example of a recursive Fibonacci function:

```python
fib = def_(lambda n: [
    if_[n <= 0] [
        raise_[ValueError(f'{n} should be positive')]
    ],
    if_[n <= 2] [
        return_[1]
    ],
    return_[fib(n - 1) + fib(n - 2)]
])
fib(10)  # 55
```

Compared with ordinary lambda, which only allows single expression as body, lambdex may contain multiple "statements" in analogue to imperative control flows, whilst does not violate the basic syntax of Python.

- [More about lambdex](#more-about-lambdex)
- Installation & Usage
- [Supported features](#supported-features)
- Known issues

## More about lambdex

An anonymous function is a function definition that is not bound to an identifier, which is ubiquitous in most languages with first-class functions. The language feature could be handy for logics that appear to be short-term use, and therefore adopted widely in some functional programming paradigms.

Python provides `lambda <arg>: <expr>` for such purpose. Lambdas are good for simple functionalities, but appear limited if complexity goes up. Consequently, higher-order functions (e.g., decorators) are often implemented as nested named functions, which is not concise enough.

`lambdex` as a complement to lambdas, aims to provide a syntax similar to Python for anonymous functions. The syntax itself is built upon valid Python expressions, and therefore requires no modification to the interpreter. Moreover, lambdexs would be compiled into Python bytecodes, and ensures the efficiency at runtime.

## Supported features

TODO

- [x] nested multi-line lambda
- [x] `return`
- [x] `pass`
- [x] `if...elif...else`
- [x] `for..in...else`
- [x] `while...else`
- [x] `break`, `continue`
- [x] chained assignments like `a <= b <= 1`
- [x] `with...as`
- [x] `raise...from`
- [x] `try...except...else...finally`
- [x] `yield` and `yield_from`
- [x] `global` and `nonlocal`
