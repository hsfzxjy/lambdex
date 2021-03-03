# Customization

**lambdex** supports user customization for both the compiler and the formatter. To customize, one should provide a config file named `.lambdex.cfg` in the file system. The file is written in INI format. **Once configured, the settings will never be changed at runtime**.

If you want to completely disable customization, simply set environment variable `LXNOCFG=1`.

List of environment variables that affect the behavior of **lambdex**:

- `LXNOCFG=1` disables any customization;
- `LXALIAS=1` enableds keyword and operator aliasing.

## Config File Resolving

**lambdex** will search for the config file in the directories specified below:

1.  All parents of the input file, if **lambdex** is run as formatter and not reading from stdin;
2.  All parents of the importer module, if **lambdex** is imported by a user script / module;
3.  CWD and all its parents.

The first one matched will be adopted. Below are several examples for better understanding.

### Example 1

Suppose **lambdex** is run as formatter (such as **lxfmt**), and two input files `/path1/to/file1.py`, `/path2/to/file2.py` supplied, and CWD is `/path3/cwd/`. The config file will be searched from (_note that the two inputs may not share a config file_):

```bash
# Search paths for input 1
/path1/to/
/path1/
/
/path3/cwd/
/path3/
/

# Search paths for input 2
/path2/to/
/path2/
/
/path3/cwd/
/path3/
/
```

### Example 2

Suppose **lambdex** is imported by `/path/to/file.py`, and CWD is `/path3/cwd/`. The config file will be searched from:

```bash
/path/to/
/path/
/
/path3/cwd/
/path3/
/
```

### Example 3

Suppose **lambdex** is imported in an REPL, and CWD is `/path3/cwd/`. The config file will be searched from:

```bash
/path3/cwd/
/path3/
/
```

## Keyword and Operator Aliasing

Aliasing allows you to use keywords and operetors other than the default ones. By default, aliasing is **disabled**. One should set environment variable `LXALIAS=1` to enable it.

Aliasing should be specified in the `[aliases]` section in `.lambdex.cfg`, e.g.

```ini
# .lambdex.cfg
[aliases]
def_ = Def
if_ = If
else_ = Else
return_ = Return
Assignment = <=
```

The configuration above allows you to write code like

```python
from lambdex import Def  # <-- Note here

max_plus_one = Def(lambda a, b: [
    If[a > b] [
        larger <= a,
    ].Else [
        larger <= b,
    ],
    Return[larger + 1]
])
```

Full list of alias entries goes here

```ini
# .lambdex.cfg
[aliases]
# Keywords
def_        = def_
if_         = if_
elif_       = elif_
else_       = else_
for_        = for_
while_      = while_
with_       = with_
try_        = try_
except_     = except_
finally_    = finally_
yield_      = yield_
yield_from_ = yield_from_
pass_       = pass_
return_     = return_
from_       = from_
raise_      = raise_
global_     = global_
nonlocal_   = nonlocal_
del_        = del_
break_      = break_
continue_   = continue_
callee_     = callee_
async_def_  = async_def_
async_with_ = async_with_
async_for_  = async_for_
await_      = await_

# Operators
# From now on, the fields should start with captialized letters
Assignment   = <
As           = >
```

## Language Extension

Extensions should be specified in the `[features]` section in `.lambdex.cfg`. To turn on a specific feature, simply set the entry to `ON`.

Full list of extensions goes here:

```ini
[features]
await_attribute = OFF
implicit_return = OFF
```
