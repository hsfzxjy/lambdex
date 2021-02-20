from typing import Sequence, List, Tuple, Optional, Dict, Union

import sys
import dis
import types
from inspect import iscode
from collections import defaultdict
from opcode import opmap, opname, stack_effect

from lambdex._aliases import get_declarers
from lambdex.utils import compat
from lambdex.ast_parser import (
    find_lambdex_ast_in_code,
    LambdexASTLookupKey,
    LambdexASTLookupTable,
)

from lambdex.compiler.core import _compile

__all__ = ['transpile']

LOAD_GLOBAL = opmap['LOAD_GLOBAL']
LOAD_NAME = opmap['LOAD_NAME']
LOAD_METHOD = opmap['LOAD_METHOD'] if sys.version_info > (3, 6, float('inf')) else opmap['LOAD_ATTR']
LOAD_CLOSURE = opmap['LOAD_CLOSURE']
LOAD_CONST = opmap['LOAD_CONST']

CALL_FUNCTION = opmap['CALL_FUNCTION']
CALL_METHOD = opmap['CALL_METHOD'] if sys.version_info > (3, 6, float('inf')) else CALL_FUNCTION

MAKE_FUNCTION = opmap['MAKE_FUNCTION']
BUILD_TUPLE = opmap['BUILD_TUPLE']

DUP_TOP = opmap['DUP_TOP']
STORE_DEREF = opmap['STORE_DEREF']

EXTENDED_ARG = opmap['EXTENDED_ARG']

JUMP_FORWARD = opmap['JUMP_FORWARD']
JUMP_ABSOLUTE = opmap['JUMP_ABSOLUTE']

JUMP_IF_TRUE_OR_POP = opmap['JUMP_IF_TRUE_OR_POP']
JUMP_IF_FALSE_OR_POP = opmap['JUMP_IF_FALSE_OR_POP']

POP_JUMP_IF_FALSE = opmap['POP_JUMP_IF_FALSE']
POP_JUMP_IF_TRUE = opmap['POP_JUMP_IF_TRUE']

JABS_STACK_EFFECT_AFTER_JUMP = {
    JUMP_ABSOLUTE: 0,
    JUMP_IF_TRUE_OR_POP: 0,
    JUMP_IF_FALSE_OR_POP: 0,
    POP_JUMP_IF_FALSE: -1,
    POP_JUMP_IF_TRUE: -1,
}
JREL_STACK_EFFECT_AFTER_JUMP = {
    JUMP_FORWARD: 0,
}
HASJABS = frozenset(dis.hasjabs)
HASJREL = frozenset(dis.hasjrel)
HASFREE = frozenset(dis.hasfree)


class _LambdexBlock:
    """
    A lambdex block is a range of bytecodes representing a lambdex definition.
    Ideally, it should cover a bytecode sequence like:

     LOAD_GLOBAL / LOAD_NAME     (def_)
    [LOAD_METHOD                 (<ident>)    ]  # Optional for def_.<ident>(...) syntax
    [...                                      ]  # Optional ops for building defaults
    [LOAD_CLOSURE                ...          ]  #
    [LOAD_CLOSURE                ...          ]  # Optional ops for building closure tuple
    [MAKE_TUPLE                               ]  #
     LOAD_CONST                  (<code>)
     LOAD_CONST                  ('<lambda>')
     MAKE_FUNCTION
     CALL_FUNCTION / CALL_METHOD
    """
    __slots__ = (
        # ====> These fields record some key offsets of the block
        # The start offset of the block (inclusive)
        # Usually a LOAD_GLOBAL / LOAD_NAME (def_)
        'offset_start',
        # The end offset of the block (inclusive)
        # Usually a CALL_FUNCTION / CALL_METHOD
        'offset_end',
        # The offset of an op from which should preserve
        # Should be the next op of `offset_start`, if using def_(...)
        # or the second next op of `offset_start`, if using def_.<ident>(...)
        'offset_start_make_lambda',
        # The offset of an op at which building closure tuple ends
        # Should be the offset of the BUILD_TUPLE, or None if no closure built
        'offset_end_make_closure_tuple',

        # ====> These fields are temporary variables during block recognizing phase,
        # ====> and has no meaning outside `_find_lambdex_blocks`
        # The stach depth BEFORE `offset_start`
        'stack_depth',
        # If a jump op met during recognizing, store the target offset in `offset_jump`,
        # and the stack depth after jumping in `stack_depth_after_jump`
        'offset_jump',
        'stack_depth_after_jump',

        # ====> These fields characterize a definition, for AST rewriting
        # The lineno of the last CALL_FUNCTION / CALL_METHOD op
        'lineno',
        # Names of freevars that the lambdex owns
        'freevars',
        # Oparg of LOAD_CLOSURE for each freevar
        'freevar_opargs',
        # The keyword of lambdex
        'keyword',
        # The identifier of lambdex
        'identifier',
        # The code object of the lambda expression
        'lambda_code',

        # ====> These fields are for bytecode rewriting
        # The index of `lambda_code` in co_consts
        'code_const_idx',
        # The arg of MAKE_FUNCTION
        'make_function_mode',
        # Storing compiled lambdex code object
        'compiled_code',
        # Freevars mapping before and after transpilation
        'fvmapping',
    )

    def __init__(self):
        self.freevars = []
        self.freevar_opargs = []
        self.identifier = None
        self.lambda_code = None
        self.offset_jump = None
        self.make_function_mode = None
        self.offset_end_make_closure_tuple = None

    def __repr__(self) -> str:
        fields = ', '.join('{}={}'.format(name, getattr(self, name, None)) for name in self.__slots__)
        return 'Def({})'.format(fields)

    @property
    def key(self) -> LambdexASTLookupKey:
        """
        A unique key for matching corresponding AST.
        """
        return (self.lineno, self.keyword, self.identifier)


def _find_lambdex_blocks(code: types.CodeType) -> Sequence[_LambdexBlock]:
    """
    Find all lambdex block in `code.co_code`.

    The returned sequence does not assume any ordering (so that you may sort by yourself).
    """
    # Storing them locally for faster accessing
    names = code.co_names
    consts = code.co_consts
    freevars = code.co_freevars
    cellvars = code.co_cellvars
    closures = cellvars + freevars

    # Variables related to offset-lineno lookup
    linestarts = list(dis.findlinestarts(code))
    i_linestarts = -1
    n_linestarts = len(linestarts)
    lineno = -1  # The current line number

    # Variables related to currently processing blocks
    # NOTE that blocks may be cascaded (e.g., another lambdex being the default arg value
    # of one lambdex), so we need a stack-like structure
    blocks = []
    curr_block = None

    stack_depth = 0  # A single integer emulating stack evolution
    prev_op = None  # The previous op

    for offset, op, arg in dis._unpack_opargs(code.co_code):
        # Update lineno if necessary
        if n_linestarts - 1 > i_linestarts and linestarts[i_linestarts + 1][0] <= offset:
            i_linestarts += 1
            lineno = linestarts[i_linestarts][1]

        # If matched a LOAD_GLOBAL / LOAD_NAME def_, start a new block
        if op in {LOAD_GLOBAL, LOAD_NAME} and names[arg] in get_declarers():
            curr_block = _LambdexBlock()
            curr_block.keyword = names[arg]
            curr_block.lineno = lineno
            curr_block.offset_start = offset
            curr_block.stack_depth = stack_depth
            curr_block.offset_start_make_lambda = offset
            blocks.append(curr_block)

        # A jump op may be encountered when building default arg values, e.g.,
        # `and`, `or` or `...if...else...` expressions.  We won't perform any
        # updates on the current block, but only discover new blocks before
        # reaching the jump target.  Before this time, the stack may be messed
        # up, so we restore the `stack_depth` after jumping.

        # We record metadata of jumping only if
        #  1) some blocks are being processed;
        #  2) the currently processed block is not jumping.
        if not blocks or curr_block.offset_jump is not None:
            pass
        elif op in HASJABS:
            effect = JABS_STACK_EFFECT_AFTER_JUMP[op]
            curr_block.offset_jump = arg
            curr_block.stack_depth_after_jump = stack_depth + effect
        elif op in HASJREL:
            effect = JREL_STACK_EFFECT_AFTER_JUMP[op]
            curr_block.offset_jump = arg + offset + 2
            curr_block.stack_depth_after_jump = stack_depth + effect

        # If reaching a jump target, we restore the stack depth
        if blocks and curr_block.offset_jump == offset:
            curr_block.offset_jump = None
            stack_depth = curr_block.stack_depth_after_jump

        # Update the stack depth as if (op, arg) is performed
        if op != EXTENDED_ARG:  # In Python <= 3.7, EXTENDED_ARG as argument will cause ValueError
            stack_depth += stack_effect(op, arg)

        # In the following branches, we update the current block and decide whether
        # the block is finished or broken
        if not blocks or curr_block.offset_jump is not None:
            pass
        elif curr_block.stack_depth >= stack_depth:
            # If the function `def_` or `def_.<ident>` popped unexpectedly,
            # we consider the current block as broken
            blocks.pop()
            if blocks: curr_block = blocks[-1]
        elif op == LOAD_METHOD and offset == curr_block.offset_start + 2:
            # If LOAD_METHOD met just after offset_start, record the name as identifier
            curr_block.identifier = names[arg]
            curr_block.offset_start_make_lambda = offset
        elif op == LOAD_CONST and iscode(consts[arg]):
            # If loading a code object, store it in `.lambda_node` (so that the last one preserved)
            curr_block.lambda_code = consts[arg]
            curr_block.code_const_idx = arg
        elif op == LOAD_CLOSURE:
            # If LOAD_CLOSURE met, record the arg as a freevar
            curr_block.freevars.append(closures[arg])
            curr_block.freevar_opargs.append(arg)
        elif prev_op == LOAD_CLOSURE and op == BUILD_TUPLE:
            # If making closure tuple, record the offset
            curr_block.offset_end_make_closure_tuple = offset
        elif op == MAKE_FUNCTION:
            # If MAKE_FUNCTION met, record the offset (so that the last one preserved)
            curr_block.make_function_mode = arg
        elif op in {CALL_FUNCTION, CALL_METHOD} and stack_depth == curr_block.stack_depth + 1:
            # If CALL_FUNCTION / CALL_METHOD met and the stack is balanced, finish the current block
            curr_block.offset_end = offset
            yield blocks.pop()
            if blocks: curr_block = blocks[-1]

        prev_op = op


class _Instruction:
    """
    Representing a bytecode instruction.

    NOTE that an instruction may be extended, that is, preceding by
    several EXTENDED_ARG op(s).  We omit all EXTENDED_ARG by squeezing
    them into the instruction behind.  An extended instruction has
    length more than 2, and its offset will be the start offset of the
    first EXTENDED_ARG. e.g.:

    0 EXTENDED_ARG   0x01
    2 JUMP_FORWARD   0x02

    will be represented by a single _Instruction:

    _Instruction(
        offset=0,
        length=4,
        op=JUMP_FORWARD,
        arg=0x102,
    )
    """
    __slots__ = (
        'op',
        'arg',
        'offset',
        'lineno',
        'is_jabs',
        'is_jrel',
        'is_jump',
        'jump_offset',
        'length',  # #bytes the instruction takes
    )

    def __init__(self, op: int, arg: int, offset: int = -1):
        self.op = op
        self.arg = arg or 0
        self._calc_length()  # Update self.length

        self.offset = offset + 2 - self.length

        self.is_jrel = op in HASJREL
        self.is_jabs = op in HASJABS
        self.is_jump = self.is_jrel or self.is_jabs
        self._calc_jump_offset()  # Update self.jump_offset

        self.lineno = None

    def _calc_jump_offset(self):
        """
        Update self.jump_offset.
        """
        if self.is_jrel:
            jump_offset = self.offset + self.arg + 2
        elif self.is_jabs:
            jump_offset = self.arg
        else:
            jump_offset = None

        self.jump_offset = jump_offset

    def _calc_length(self):
        """
        Update self.length.
        """
        arg = self.arg
        if not arg:
            length = 2
        else:
            length = 0
            # There would be a case that arg < 0 when offset of jump target
            # is -1 (uninitialized)
            while arg > 0:
                arg >>= 8
                length += 2
        self.length = length

    def assemble(self) -> Sequence[int]:
        """
        Return the bytes sequence of this instruction.
        """
        arg = self.arg or 0
        length = self.length // 2
        for i, byte in enumerate(arg.to_bytes(length, 'little')):
            yield EXTENDED_ARG if i < length - 1 else self.op
            yield byte

    def update(self, jtable: '_JumpTable', offset: int) -> bool:
        """
        Update self.offset and self.arg given a new offset and jump table.

        Return True if either of the fields is renewed; False otherwise.
        """
        changed = offset != self.offset
        self.offset = offset
        if self.is_jabs:
            new_arg = jtable[self].offset
        elif self.is_jrel:
            new_arg = jtable[self].offset - self.offset - 2
        else:
            self._calc_length()
            return changed

        changed = changed or self.arg != new_arg
        self.arg = new_arg
        self._calc_length()
        self._calc_jump_offset()
        return changed

    def jump_offset_is_wrong(self, jtable: '_JumpTable') -> bool:
        """
        Given a jump table, check whether self.jump_offset is correct or not.
        """
        return self.is_jump and self.jump_offset != jtable[self].offset

    def __repr__(self):
        return '{}{}{}'.format(str(self.offset).rjust(20), opname[self.op].rjust(20), str(self.arg).rjust(20))


class _JumpTable:
    """
    An object maintaining the mapping between jump sources and targets.

    A _JumpTable preserves the mapping in both directions, so that updating
    jump targets could have constant time complexity.
    """
    def __init__(self, instrs: Sequence[_Instruction]):
        """
        `instrs` should be well-behaved, i.e., the `.jump_offset` of each 
        instruction correctly equals the offset of its target.

        Usually, `instrs` should be the instruction sequence just disassembled
        from a code object.
        """
        self._mapping = {}
        self._reversed_mapping = defaultdict(set)

        offset2instr = {}
        pairs = []
        for instr in instrs:
            offset2instr[instr.offset] = instr
            if instr.jump_offset is not None:
                pairs.append((instr.offset, instr.jump_offset))

        for source_offset, target_offset in pairs:
            source = offset2instr[source_offset]
            target = offset2instr[target_offset]
            self._mapping[source] = target
            self._reversed_mapping[target].add(source)

    def replace(self, old: _Instruction, new: _Instruction):
        """
        Replace instruction `old` with instruction `new`, while
        not violating the mapping.
        """
        # Do nothing if old and new are same objects
        if old is new: return

        m, rm = self._mapping, self._reversed_mapping

        popped = m.pop(old, None)
        if popped is not None:
            m[new] = popped
            rm[popped].remove(old)
            rm[popped].add(new)

        popped = rm.pop(old, None)
        if popped is not None:
            rm[new] = popped
            for item in popped:
                m[item] = new

    def __getitem__(self, instr: _Instruction) -> _Instruction:
        """
        Return the jump target of a given instruction.
        """
        return self._mapping[instr]

    def __repr__(self) -> str:
        lines = ('{} -> {}'.format(k, v) for k, v in self._mapping.items())
        return '\n'.join(lines)


def _disassemble(code: types.CodeType) -> Tuple[List[_Instruction], _JumpTable]:
    """
    Disassemble `code` into sequence of _Instruction. Also build up the jump table.
    """
    instrs = []
    linestarts = dict(dis.findlinestarts(code))
    for offset, op, arg in dis._unpack_opargs(code.co_code):
        if op == EXTENDED_ARG:
            continue
        instr = _Instruction(op, arg, offset)
        instr.lineno = linestarts.get(instr.offset)
        instrs.append(instr)

    table = _JumpTable(instrs)
    return instrs, table


def _assemble(instrs: Sequence[_Instruction]) -> bytes:
    """
    Produce bytecodes from a sequence of _Instruction.
    """
    def _iter():
        for item in instrs:
            yield from item.assemble()

    return bytes(_iter())


def _calibrate_offsets(instrs: List[_Instruction], jtable: _JumpTable):
    """
    Calibrate offsets and jump targets for all instructions in `instrs`.
    """
    # We perform the calibration in an iterative way, since updating an arg may change
    # the length of the instruction and further change the offsets of instructions behind it.
    changed = True
    while changed:
        offset = 0
        changed = False
        for instr in instrs:
            changed = changed or instr.update(jtable, offset)
            offset += instr.length

        # If nothing updated in this iteration, we perform a checking over all instructions
        # The checking is short-curcuited, so that we don't need to iterate over the whole
        # list if violation exists
        if not changed and any(item.jump_offset_is_wrong(jtable) for item in instrs):
            changed = True


def _rewrite_code(
    code: types.CodeType,
    asttab: LambdexASTLookupTable,
) -> Tuple[bytes, List, List, bytes, List[int]]:
    """
    Rewrite `code` to eliminate lambdex runtime transpiling.
    
    Firstly, the function find all blocks in `code.co_code`. For each block, the following
    steps are taken:

    1) remove LOAD_NAME / LOAD_GLOBAL / LOAD_METHOD at the start;
    2) create a new cellvar at the back of co_cellvars to store the generated function;
    3) rebuild the closure tuple to make sure it matches the order of the new co_freevars;
    4) store the compiled code object where the original lambda code object was stored;
    5) create a new const at the back of co_consts, and make the last LOAD_CONST <qualname>
       point to it;
    6) remove the last CALL_FUNCTION / CALL METHOD, insert the following sequence:
            DUP_TOP
            STORE_DEREF <new cellvar idx>
       so that the new generated function is stored into the new cellvar.

    After the new instructions settled, the function calibrate the offsets and the lineno table
    to make sure they are well-behaved.

    Returns:
     - new_bytecodes (bytes)
     - new_consts (list)
     - new_cellvars (list)
     - new_lnotab (bytes)
     - skipped_consts_idxs (list): indices of the code objects that need not to be rewritten.
    """
    def _calibrate_freevar_index(instr: _Instruction) -> _Instruction:
        # calibrate freevar index, since we will change the length of co_cellvars
        if instr.op in HASFREE:
            if instr.arg >= ncellvars:
                instr.arg += nblocks
        return instr

    old_instrs, jtable = _disassemble(code)
    old_instrs = iter(map(_calibrate_freevar_index, old_instrs))

    new_instrs = []
    skipped_const_idxs = []

    # Currently handling blocks
    hblocks = []
    # Remaining blocks to be handled
    rblocks = _find_lambdex_blocks(code)

    # Sort rblocks by starting offset descendingly.
    # Since new block are popped from rblocks, blocks at the left will be handled first
    rblocks = sorted(rblocks, key=lambda x: x.offset_start, reverse=True)
    nblocks = len(rblocks)

    # Store the variables locally for faster accessing
    # The tuples are casted into lists to allow mutation
    consts = list(code.co_consts)
    cellvars = list(code.co_cellvars or [])
    ncellvars = len(cellvars)

    # The index of item if new items were to added
    extra_closure_idx = len(cellvars)
    extra_const_idx = len(consts)

    curr_block = None  # Short-hand for hblocks[-1]

    discarded_instrs = []

    while rblocks or hblocks:
        try:
            curr_instr = next(old_instrs)
        except StopIteration:
            # Usually the end of a block will not be at the last
            # If this happens, complain it
            raise EOFError('Unexpected end of bytecodes encounted')

        offset = curr_instr.offset

        # If we reach the beginning of a block
        if rblocks and offset >= rblocks[-1].offset_start:
            # marked it as handling
            curr_block = rblocks.pop()
            hblocks.append(curr_block)

            # Use the block key to find corresponding AST, and obtained
            # the compiled code object
            astdef = asttab[curr_block.key]
            lambdex_code, _, fvmapping = _compile(astdef, code.co_filename, curr_block.freevars)

            curr_block.compiled_code = lambdex_code
            curr_block.fvmapping = fvmapping
            consts[curr_block.code_const_idx] = lambdex_code

            # Mark the compiled code object as skipped
            skipped_const_idxs.append(curr_block.code_const_idx)

        # If we bypass the end of a block, remove it from hblocks
        if curr_block is not None and offset > curr_block.offset_end:
            hblocks.pop()
            curr_block = hblocks[-1] if hblocks else None

        # NOTE: From now on, curr_instr may be discarded, and new instructions may be inserted
        # before or after it.  We want to transfer the lineno of curr_instr onto the first added
        # instruction, as well as maintaining the jump mapping.

        first_added_instr = None
        if curr_block is None:
            # If no block handling, simply append curr_instr
            new_instrs.append(curr_instr)
            first_added_instr = curr_instr
        elif offset <= curr_block.offset_start_make_lambda:
            # Remove preceding LOAD_GLOBAL / LOAD_NAME / LOAD_METHOD
            pass
            discarded_instrs.append(curr_instr)
        elif curr_instr.op == LOAD_CLOSURE:
            # Remove all LOAD_CLOSURE's (and rebuild later)
            pass
            discarded_instrs.append(curr_instr)
        elif curr_block.offset_end_make_closure_tuple == offset:
            # If reached the BUILD_TUPLE, build the new closure tuple
            for newidx, oldidx in enumerate(curr_block.fvmapping):
                if oldidx == -1:
                    oparg = extra_closure_idx
                    should_calibrate = False
                else:
                    oparg = curr_block.freevar_opargs[oldidx]
                    should_calibrate = True
                instr = _Instruction(LOAD_CLOSURE, oparg)
                if should_calibrate:
                    _calibrate_freevar_index(instr)

                new_instrs.append(instr)

                if newidx == 0:
                    first_added_instr = instr

            curr_instr.arg = len(curr_block.fvmapping)
            new_instrs.append(curr_instr)

            discarded_instrs.append(curr_instr)
        elif offset == curr_block.offset_end - 6 and curr_block.offset_end_make_closure_tuple is None:
            # If no closure was made in the code bytecodes, make one
            new_instrs.append(_Instruction(LOAD_CLOSURE, extra_closure_idx))
            first_added_instr = new_instrs[-1]

            new_instrs.append(_Instruction(BUILD_TUPLE, 1))
            new_instrs.append(curr_instr)

            discarded_instrs.append(curr_instr)
        elif offset == curr_block.offset_end - 4:
            # If reached LOAD_CONST <qualname>
            curr_instr.arg = extra_const_idx
            new_instrs.append(curr_instr)
            first_added_instr = curr_instr

            consts.append(curr_block.compiled_code.co_name)
            extra_const_idx += 1
        elif offset == curr_block.offset_end - 2:
            # If reached MAKE_FUNCTION
            curr_instr.arg |= 0x08  # built with closure
            new_instrs.append(curr_instr)
            first_added_instr = new_instrs[-1]
        elif offset == curr_block.offset_end:
            # If reached CALL_FUNCTION / CALL_METHOD of def_
            new_instrs.append(_Instruction(DUP_TOP, 0x00))
            first_added_instr = new_instrs[-1]

            new_instrs.append(_Instruction(STORE_DEREF, extra_closure_idx))

            cellvars.append('?')  # the name need not to be valid, since its just a placeholder
            extra_closure_idx += 1

            discarded_instrs.append(curr_instr)
        else:
            # Otherwise
            new_instrs.append(curr_instr)
            first_added_instr = curr_instr

        # Maintain lineno and jump mapping
        if first_added_instr is not None:
            for item in discarded_instrs:
                jtable.replace(item, first_added_instr)
                if not first_added_instr.lineno:
                    first_added_instr.lineno = item.lineno
            discarded_instrs.clear()

    # If there are more instructions, simply append them
    new_instrs.extend(old_instrs)

    _calibrate_offsets(new_instrs, jtable)

    new_bytecodes = _assemble(new_instrs)
    new_lnotab = _make_lnotab(new_instrs, code.co_firstlineno)

    return new_bytecodes, consts, cellvars, new_lnotab, skipped_const_idxs


# From Python 3.10+, there would be a new linetable specification
# See https://github.com/python/cpython/blob/v3.10.0a5/Objects/lnotab_notes.txt
if sys.version_info > (3, 9, float('inf')):

    def _make_lnotab(instrs: List[_Instruction], firstlineno: int) -> Dict[str, bytes]:
        """
        Generate co_lnotab byte sequence from `instrs`.
        """
        def _iter() -> Sequence[int]:
            ldelta = None
            prev_lineno = firstlineno or 0
            start = 0
            end = None

            class sentinel:
                offset = instrs[-1].offset
                lineno = instrs[-1].lineno

            for instr in instrs + [sentinel]:
                if instr.lineno is None and instr is not sentinel:
                    continue
                offset = instr.offset
                lineno = instr.lineno
                if start is None:
                    start = offset
                else:
                    end = offset

                sdelta = end - start
                while sdelta > 0xfe:
                    yield 0xfe
                    yield 0x00
                    sdelta -= 0xfe
                yield sdelta
                if ldelta is None:
                    yield 0x80
                elif -127 <= ldelta <= -1:
                    yield ldelta + 0x100
                elif 0 <= ldelta <= 127:
                    yield ldelta
                elif ldelta < -127:
                    yield 0x81
                    ldelta += 127
                    while ldelta < -127:
                        yield 0x00
                        yield 0x81
                        ldelta += 127
                    yield 0x00
                    yield ldelta + 0x100
                else:
                    yield 0x7f
                    ldelta -= 127
                    while ldelta > 127:
                        yield 0x00
                        yield 0x7f
                        ldelta -= 127
                    yield 0x00
                    yield ldelta

                start = end
                end = None
                ldelta = lineno - prev_lineno if lineno else None
                prev_lineno = lineno
            yield 0xff
            yield 0x00

        return dict(co_linetable=bytes(_iter()))
else:

    def _make_lnotab(instrs: Sequence[_Instruction], firstlineno: int) -> Dict[str, bytes]:
        """
        Generate co_lnotab byte sequence from `instrs`.
        """
        def _iter() -> Sequence[int]:
            prev_offset = 0
            prev_lineno = firstlineno or 0
            for instr in instrs:
                if instr.lineno is None: continue
                offset = instr.offset
                lineno = instr.lineno

                sdelta = offset - prev_offset
                ldelta = lineno - prev_lineno
                while sdelta > 0xff:
                    yield 0xff
                    yield 0x00
                    sdelta -= 0xff
                yield sdelta
                if -128 <= ldelta <= -1:
                    yield ldelta + 0x100
                elif 0 <= ldelta <= 127:
                    yield ldelta
                elif ldelta < -128:
                    yield 0x80
                    ldelta += 128
                    while ldelta < -128:
                        yield 0x00
                        yield 0x80
                        ldelta += 128
                    yield 0x00
                    yield ldelta + 0x100
                else:
                    yield 0x7f
                    ldelta -= 127
                    while ldelta > 127:
                        yield 0x00
                        yield 0x7f
                        ldelta -= 127
                    yield 0x00
                    yield ldelta

                prev_offset = offset
                prev_lineno = lineno

        return dict(co_lnotab=bytes(_iter()))


def transpile(code: types.CodeType, ismod: bool, asttab: Optional[LambdexASTLookupTable] = None) -> types.CodeType:
    """
    Recursively rewrite `code` to eliminate lambdex runtime compiling.
    """
    if asttab is None:
        asttab = find_lambdex_ast_in_code(code, ismod)

    new_bc, new_consts, new_cellvars, new_lnotab, skipped_const_idxs = _rewrite_code(code, asttab)

    for idx, const in enumerate(new_consts):
        if idx in skipped_const_idxs: continue
        if iscode(const):
            new_consts[idx] = transpile(const, asttab)

    return compat.code_replace(
        code,
        co_code=new_bc,
        co_consts=tuple(new_consts),
        co_cellvars=tuple(new_cellvars),
        **new_lnotab,
    )
