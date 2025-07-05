from enum import Enum, Flag, auto
from typing import Tuple, Any
import array
import io
import struct


# general class of instruction
class ITYPE(Enum):
    ALU = 1
    SHORT_BRANCH = 2
    SHORT_OR_LONG_BRANCH = 3
    LONG_BRANCH = 4

# argument types
class ATYPE(Enum):
    NONE      = 0  # nop
    DAB       = 1  # add D, A, B
    DAB_LS    = 2  # ldr r0, r1, r2
    DB        = 3  # add D, B    --- add D, r0, B
    D         = 4  # b   D
    DA_MINUS1 = 5  # not D, A    --- xor D, A, #-1
    AB        = 6  # tst A, B    --- xor r0, A, B

# flags for instruction formats
class IFORMAT_FLAG(Flag):
    NONE = 0
    FORCE_B = auto()  # force argument into the B slot, even if it's a register

class IFormat:
    def __init__(self, opcode : int, itype : ITYPE, atype : ATYPE, flags : IFORMAT_FLAG = IFORMAT_FLAG.NONE):
        self.opcode = opcode
        self.itype = itype
        self.atype = atype
        self.flags = flags

opcode_table = {
    'mov': IFormat(0b00000 << 11, ITYPE.ALU, ATYPE.DB),
    'add': IFormat(0b00001 << 11, ITYPE.ALU, ATYPE.DAB),
    'adc': IFormat(0b00010 << 11, ITYPE.ALU, ATYPE.DAB),
    'sub': IFormat(0b00011 << 11, ITYPE.ALU, ATYPE.DAB),
    'sbc': IFormat(0b00100 << 11, ITYPE.ALU, ATYPE.DAB),
    'and': IFormat(0b00101 << 11, ITYPE.ALU, ATYPE.DAB),
    'or':  IFormat(0b00110 << 11, ITYPE.ALU, ATYPE.DAB),
    'xor': IFormat(0b00111 << 11, ITYPE.ALU, ATYPE.DAB),
    'lsl': IFormat(0b01000 << 11, ITYPE.ALU, ATYPE.DAB),
    'lsr': IFormat(0b01001 << 11, ITYPE.ALU, ATYPE.DAB),
    'asr': IFormat(0b01010 << 11, ITYPE.ALU, ATYPE.DAB),
    'ror': IFormat(0b01011 << 11, ITYPE.ALU, ATYPE.DAB),

    'ldr': IFormat(0b01100 << 11, ITYPE.ALU, ATYPE.DAB_LS),
    'str': IFormat(0b01101 << 11, ITYPE.ALU, ATYPE.DAB_LS),

  #'push': IFormat(0b01110 << 11, ITYPE.ITYPE_ALU, ATYPE.DAB),
   #'pop': IFormat(0b01111 << 11, ITYPE.ITYPE_ALU, ATYPE.DAB),

    'beq': IFormat(0b10000 << 11 | (0b0000 << 10), ITYPE.SHORT_BRANCH, ATYPE.D),
    'bne': IFormat(0b10000 << 11 | (0b0001 << 10), ITYPE.SHORT_BRANCH, ATYPE.D),
    'bcs': IFormat(0b10000 << 11 | (0b0010 << 10), ITYPE.SHORT_BRANCH, ATYPE.D),
    'bhs': IFormat(0b10000 << 11 | (0b0010 << 10), ITYPE.SHORT_BRANCH, ATYPE.D), # same as bcs
    'bcc': IFormat(0b10000 << 11 | (0b0011 << 10), ITYPE.SHORT_BRANCH, ATYPE.D),
    'blo': IFormat(0b10000 << 11 | (0b0011 << 10), ITYPE.SHORT_BRANCH, ATYPE.D), # same as bcc
    'bmi': IFormat(0b10000 << 11 | (0b0100 << 10), ITYPE.SHORT_BRANCH, ATYPE.D),
    'bpl': IFormat(0b10000 << 11 | (0b0101 << 10), ITYPE.SHORT_BRANCH, ATYPE.D),
    'bvs': IFormat(0b10000 << 11 | (0b0110 << 10), ITYPE.SHORT_BRANCH, ATYPE.D),
    'bvc': IFormat(0b10000 << 11 | (0b0111 << 10), ITYPE.SHORT_BRANCH, ATYPE.D),
    'bhi': IFormat(0b10000 << 11 | (0b1000 << 10), ITYPE.SHORT_BRANCH, ATYPE.D),
    'bls': IFormat(0b10000 << 11 | (0b1001 << 10), ITYPE.SHORT_BRANCH, ATYPE.D),
    'bge': IFormat(0b10000 << 11 | (0b1010 << 10), ITYPE.SHORT_BRANCH, ATYPE.D),
    'blt': IFormat(0b10000 << 11 | (0b1011 << 10), ITYPE.SHORT_BRANCH, ATYPE.D),
    'bgt': IFormat(0b10000 << 11 | (0b1100 << 10), ITYPE.SHORT_BRANCH, ATYPE.D),
    'ble': IFormat(0b10000 << 11 | (0b1101 << 10), ITYPE.SHORT_BRANCH, ATYPE.D),
    'b':   IFormat(0b10000 << 11 | (0b1110 << 10), ITYPE.SHORT_OR_LONG_BRANCH, ATYPE.D),
    'bl':  IFormat(0b10000 << 11 | (0b1110 << 10) | (1<<9), ITYPE.LONG_BRANCH, ATYPE.D),

    'nop': IFormat(0b00000 << 11, ITYPE.ALU, ATYPE.NONE), # mov r0, r0

    # pseudo instructions
    'neg': IFormat(0b00011 << 11, ITYPE.ALU, ATYPE.DB, IFORMAT_FLAG.FORCE_B), # sub d, r0, b or sub d, r0, d
    'not': IFormat(0b00111 << 11, ITYPE.ALU, ATYPE.DA_MINUS1), # xor d, a, #-1
    'teq': IFormat(0b00111 << 11, ITYPE.ALU, ATYPE.AB), # xor r0, a, b
    'tst': IFormat(0b00101 << 11, ITYPE.ALU, ATYPE.AB), # and r0, a, b
    'cmp': IFormat(0b00011 << 11, ITYPE.ALU, ATYPE.AB), # sub r0, a, b
    'cmn': IFormat(0b00001 << 11, ITYPE.ALU, ATYPE.AB), # add r0, a, b
}

class FIXUP_TYPE(Enum):
    NONE = 0
    SHORT_BRANCH = 1
    LONG_BRANCH = 2
    SYMBOL_LONG = 3
    DATA_SYMBOL_LONG = 4

class Symbol:
    def __init__(self, name : str) -> None:
        self.name = name
        self.addr = 0
        self.resolved = False

    def __str__(self):
        return "Symbol '%s' at addr 0x%04x resolved %d" % (self.name, self.addr, self.resolved)

class OutputData:
    def __init__(self) -> None:
        self.addr = 0
        self.length = 0
        self.string = ""
        self.fixup_type = FIXUP_TYPE.NONE
        self.fixup_sym : Symbol | None = None

    def write_hex(self, outfile : io.IOBase):
        raise NotImplementedError("write_hex not implemented in OutputData")

    def write_hex2(self, outfile : io.IOBase):
        raise NotImplementedError("write_hex not implemented in OutputData")

    def write_bin(self, outfile : io.IOBase):
        raise NotImplementedError("write_hex not implemented in OutputData")

class Instruction(OutputData):
    def __init__(self) -> None:
        super().__init__()
        self.op = 0
        self.op2 = 0

    def write_hex(self, outfile : io.IOBase):
        outfile.write("%04x // 0x%04x %s\n" % (self.op, self.addr, self.string))
        if self.length == 2:
            outfile.write("%04x\n"  % (self.op2))

    def write_hex2(self, outfile : io.IOBase):
        outfile.write("0x%04x, // 0x%04x %s\n" % (self.op, self.addr, self.string))
        if self.length == 2:
            outfile.write("0x%04x,\n"  % (self.op2))

    def write_bin(self, outfile : io.IOBase):
        outfile.write(struct.pack('>H', self.op))
        if self.length == 2:
            outfile.write(struct.pack('>H', self.op2))

    def __str__(self):
        return "Instruction op 0x%004x 0x%04x, address 0x%04x '%s' fixup type %s sym: %s" % (
                self.op, self.op2, self.addr, self.string, str(self.fixup_type), str(self.fixup_sym))

class Data(OutputData):
    def __init__(self) -> None:
        super().__init__()
        self.data = array.array('H')

    def write_hex(self, outfile : io.IOBase):
        for i in range(self.length):
            if i == 0:
                outfile.write("%04x // 0x%04x %s\n" % (self.data[i], self.addr, self.string))
            else:
                outfile.write("%04x\n" % self.data[i])

    def write_hex2(self, outfile : io.IOBase):
        for i in range(self.length):
            if i == 0:
                outfile.write("0x%04x, // 0x%04x %s\n" % (self.data[i], self.addr, self.string))
            else:
                outfile.write("0x%04x,\n" % self.data[i])

    def write_bin(self, outfile : io.IOBase):
        for i in range(self.length):
            outfile.write(struct.pack('>H', self.data[i]))

    def __str__(self):
        return "Data '%s', address 0x%04x '%s' fixup type %s sym: %s" % (
                self.data, self.addr, self.string, str(self.fixup_type), str(self.fixup_sym))

class Codegen_Exception(Exception):
    def __init__(self, string: str) -> None:
        self.string = string

    def __str__(self):
        return self.string

def parse_tuple_to_string(t : tuple[str, int]) -> str:
    if t[0] == 'REGISTER':
        if t[1] == 8: return "lr"
        elif t[1] == 9: return "sp"
        elif t[1] == 10: return "pc"
        elif t[1] == 11: return "cr"
        else: return "r%u" % t[1]
    elif t[0] == 'NUMBER':
        return "%#x" % t[1]
    elif t[0] == 'ID':
        return str(t[1])
    else:
        return "unk"

def parse_ins_to_string(ins : str, args) -> str:
    if len(args) == 0:
        return "%s" % ins
    elif len(args) == 1:
        return "%s %s" % (ins,
            parse_tuple_to_string(args[0]))
    elif len(args) == 2:
        return "%s %s, %s" % (ins,
            parse_tuple_to_string(args[0]),
            parse_tuple_to_string(args[1]))
    elif len(args) == 3:
        return "%s %s, %s, %s" % (ins,
            parse_tuple_to_string(args[0]),
            parse_tuple_to_string(args[1]),
            parse_tuple_to_string(args[2]))
    return "unk"

class Codegen:
    def __init__(self) -> None:
        self.cur_addr : int = 0
        self.output : list[OutputData] = []
        self.symbols : dict[str, Symbol]  = {}
        self.verbose : bool = False
        pass

    def add_label(self, label : str):
        if self.verbose: print("add label %s, address %#x" % (label, self.cur_addr))

        # see if it already exists
        try:
            sym = self.symbols[label]
            if sym.resolved:
                raise Codegen_Exception("add_label: already seem symbol %s" % label)

            # it's now resolved
            sym.addr = self.cur_addr
            sym.resolved = True
        except:
            # previously unseen symbol
            sym = Symbol(label)
            sym.addr = self.cur_addr
            sym.resolved = True
            self.symbols[label] = sym

    # grab a reference to a symbol when an instruction sees a label
    def get_symbol_ref(self, label : str) -> Symbol:
        try:
            sym = self.symbols[label]
            return sym
        except KeyError:
            # previously unseen symbol
            sym = Symbol(label)
            self.symbols[label] = sym
            return sym

    def add_directive(self, ins : str, args : tuple[str, ...]):
        if self.verbose: print("add directive %s" % str(ins))
        if ins == ".word":
            d = Data()
            d.addr = self.cur_addr
            d.length = 1
            if args[0][0] == 'NUMBER':
                num = int(args[0][1])
                d.string = ".word %04x" % num
                d.data.append(num)
            elif args[0][0] == 'ID':
                # 16 bit long address, target is unresolved
                d.fixup_type = FIXUP_TYPE.DATA_SYMBOL_LONG;
                d.fixup_sym = self.get_symbol_ref(args[0][1])
                d.string = ".word %s" % args[0][1]
            self.output.append(d)
            self.cur_addr += d.length
        elif ins in { ".ascii", ".asciiz" }:
            if type(args[0]) is not str:
                raise Codegen_Exception("add_directive: .ascii used without string")

            d = Data()
            d.string = "%s '%s'" % (ins, args[0])
            d.addr = self.cur_addr

            for c in args[0]:
                d.data.append(ord(c))
            if ins == ".asciiz":
                d.data.append(0)

            d.length = len(d.data)

            self.output.append(d)
            self.cur_addr += d.length
        elif ins in { ".asciib", ".asciibz" }:
            if type(args[0]) is not str:
                raise Codegen_Exception("add_directive: .asciib used without string")

            # null terminate and make sure string length is a multiple of 2
            s = args[0]
            if ins == ".asciibz":
                s += '\0'
            if len(s) % 2:
                s += '\0'

            d = Data()
            d.addr = self.cur_addr
            d.data.frombytes(s.encode('utf-8'))
            d.string = "%s '%s'" % (ins, args[0])
            d.length = len(d.data)

            self.output.append(d)
            self.cur_addr += d.length
        else:
            raise Codegen_Exception("add_directive: unknown directive '%s'" % ins)

    def add_instruction(self, ins :str, args : Tuple[Tuple[str, int], ...]):
        if self.verbose: print("add instruction %s, args %s" % (str(ins), str(args)))

        i = Instruction()
        i.addr = self.cur_addr

        # lookup the opcode
        try:
            op = opcode_table[ins]
        except:
            raise Codegen_Exception("add_instruction: unknown instruction '%s'" % ins[0])

        i.op = op.opcode
        i.length = 1

        arg_count = len(args)

        # switch based on type
        if (op.itype == ITYPE.ALU):
            # set the default args
            dest_arg : Tuple[str, int] = ('REGISTER', 0)  # default to r0
            a_arg : Tuple[str, int] = ('REGISTER', 0)  # default to r0
            b_arg : Tuple[str, int] = ('NUMBER', 0)  # default to 0

            # match args based on instruction atype
            match = False
            if op.atype == ATYPE.NONE:
                #ATYPE_NONE - nop
                if arg_count == 0:
                    match = True
            elif op.atype == ATYPE.DAB:
                if arg_count == 3:      # add D, A, B
                    dest_arg = args[0]
                    a_arg = args[1]
                    b_arg = args[2]
                    match = True
                elif arg_count == 2:    # add D, D, B
                    dest_arg = args[0]
                    a_arg = args[0]
                    b_arg = args[1]
                    match = True
                elif arg_count == 1:    # add D, D, D
                    dest_arg = args[0]
                    a_arg = args[0]
                    b_arg = args[0]
                    match = True
            elif op.atype == ATYPE.DAB_LS:
                if arg_count == 3:      # ldr D, A, B
                    dest_arg = args[0]
                    a_arg = args[1]
                    b_arg = args[2]
                    match = True
                elif arg_count == 2:    # ldr D, B, r0 or ldr D, r0, IMM
                    dest_arg = args[0]
                    # if its two arg, assign immediate to B slot, register to A slot
                    if args[1][0] == 'REGISTER':
                        a_arg = args[1]
                    else:
                        b_arg = args[1]
                    match = True
                elif arg_count == 1:    # ldr D, D, r0
                    dest_arg = args[0]
                    a_arg = args[0]
                    match = True
            elif op.atype == ATYPE.DB:
                #ATYPE_DB - add D, B    --- add D, r0, B
                if arg_count == 2:
                    dest_arg = args[0]
                    temp_arg = args[1]
                    match = True
                elif arg_count == 1:
                    dest_arg = args[0]
                    temp_arg = args[0]
                    match = True
                else:
                    raise Codegen_Exception("add_instruction: invalid number of args for ATYPE_DB")

                # if its regster to register, use the a slot, and assign immediate to b
                # note IFORMAT_FLAG_FORCE_B is used to force the b_arg into the b slot
                if match and temp_arg[0] == 'REGISTER' and not IFORMAT_FLAG.FORCE_B in op.flags:
                    a_arg = temp_arg
                else:
                    b_arg = temp_arg
            elif op.atype == ATYPE.D:
                #ATYPE_D - b   D
                if arg_count == 1:
                    dest_arg = args[0]
                    match = True
            elif op.atype == ATYPE.DA_MINUS1:
                #ATYPE_DA_MINUS1 - not D, A    --- xor D, A, #-1
                if arg_count == 2:
                    dest_arg = args[0]
                    a_arg = args[1]
                    b_arg = ('NUMBER', -1)
                    match = True
                elif arg_count == 1:
                    dest_arg = args[0]
                    a_arg = args[0]
                    b_arg = ('NUMBER', -1)
                    match = True
            elif op.atype == ATYPE.AB:
                #ATYPE_AB - tst A, B    --- xor r0, A, B
                if arg_count == 2:
                    a_arg = args[0]
                    b_arg = args[1]
                    match = True
                elif arg_count == 1:
                    a_arg = args[0]
                    b_arg = args[0]
                    match = True

            if not match:
                raise Codegen_Exception("add_instruction: failed to match atype")

            d_special = False
            a_special = False

            if self.verbose: print("add_instruction post processing dest %s, a %s, b %s" % (str(dest_arg), str(a_arg), str(b_arg)))

            # construct the instruction out of the ops
            # destination has to be a register
            # if it's a special register, chop the top bit off and we'll deal with it in the b field
            if dest_arg[0] == 'REGISTER':
                i.op |= (dest_arg[1] & 0x7) << 8
                if dest_arg[1] >= 8: d_special = True
            else:
                raise Codegen_Exception("add_instruction: dest is bogus type '%s'" % str(dest_arg))

            # a arg can only be register
            # if it's a special register, chop the top bit off and we'll deal with it in the b field
            if a_arg[0] == 'REGISTER':
                i.op |= (a_arg[1] & 0x7) << 5
                if a_arg[1] >= 8: a_special = True
            else:
                raise Codegen_Exception("add_instruction: a is bogus type '%s'" % str(a_arg))

            # b arg can be any type, unless a or d is a special reg,
            # then b can only be an immediate
            if b_arg[0] == 'REGISTER':
                if d_special or a_special:
                    raise Codegen_Exception("add_instruction: b cannot be register with special d or a");
                i.op |= (0b10 << 3) | b_arg[1]
            elif b_arg[0] == 'NUMBER':
                num = int(b_arg[1])

                # if no special regs, and the immediate fits in 4 bits
                if not d_special and not a_special and num < 8 and num >= -7:
                    # we can use 4 bit immediate
                    i.op |= (0 << 4) | (num & 0xf)
                else:
                    # if either d or a is special, we'll need to reuse the b field to encode it
                    i.op |= (0b11 << 3)
                    if a_special: i.op |= (1 << 0)
                    if d_special: i.op |= (1 << 1)
                    if num != 0:
                        # going to have to use a full 16 bit immediate
                        i.op |= (1 << 2)
                        i.op2 = num & 0xffff
                        i.length = 2
            elif b_arg[0] == 'ID':
                # store the eventual absolute address
                i.fixup_type = FIXUP_TYPE.SYMBOL_LONG
                i.fixup_sym = self.get_symbol_ref(b_arg[1]) # type: ignore

                # if either d or a is special, we'll need to reuse the b field to encode it
                i.op |= (0b11 << 3)
                if a_special: i.op |= (1 << 0)
                if d_special: i.op |= (1 << 1)

                # going to have to use a full 16 bit immediate
                i.op |= (1 << 2)
                i.op2 = 0 # patched later
                i.length = 2
            else:
                raise Codegen_Exception("add_instruction: b is bogus type '%s'" % str(b_arg))
        elif op.itype == ITYPE.SHORT_BRANCH or op.itype == ITYPE.LONG_BRANCH or op.itype == ITYPE.SHORT_OR_LONG_BRANCH:
            # handle branches
            if arg_count != 1:
                raise Codegen_Exception("add_instruction: invalid number of args for branch")

            arg = args[0]

            # see what form it is
            long_branch = False
            if op.itype == ITYPE.LONG_BRANCH:
                long_branch = True
            elif op.itype == ITYPE.SHORT_OR_LONG_BRANCH:
                # further tests
                if arg[0] == 'REGISTER':
                    long_branch = True
                elif arg[0] == 'NUMBER' and (arg[1] >= 512 or arg[1] < -512):
                    long_branch = True
                elif arg[0] == 'ID':
                    # XXX hack, for now make all label branches long form
                    long_branch = True

            # deal with branch types
            if not long_branch:
                # short branch
                if arg[0] == 'REGISTER':
                    raise Codegen_Exception("add_instruction: register on short branch")
                elif arg[0] == 'NUMBER':
                    if arg[1] >= 512 or arg[1] < -512:
                        raise Codegen_Exception("add_instruction: short branch with too large offset %d" % int(arg[1]))
                    # it's a short immediate, just encode the instruction
                    i.op |= (int(arg[1]) & 0x3ff)
                elif arg[0] == 'ID':
                    # short branch, target is unresolved
                    i.fixup_type = FIXUP_TYPE.SHORT_BRANCH
                    i.fixup_sym = self.get_symbol_ref(arg[1]) # type: ignore
            else:
                # long branch
                i.op |= (0xf << 10); # use NV condition

                if arg[0] == 'REGISTER':
                    # its a register branch
                    if (arg[1] == 0):
                        raise Codegen_Exception("add_instruction: cannot generate register branch with r0")
                    i.op |= arg[1]
                elif arg[0] == 'NUMBER':
                    # it's a 16bit signed immediate 2-word branch
                    i.op2 = (arg[1] & 0xffff)
                    i.length += 1
                elif arg[0] == 'ID':
                    # 16 bit long address, target is unresolved
                    i.op2 = 0
                    i.length += 1
                    i.fixup_type = FIXUP_TYPE.LONG_BRANCH
                    i.fixup_sym = self.get_symbol_ref(arg[1]) # type: ignore
                    pass
        else:
            raise Codegen_Exception("add_instruction: unhandled ITYPE")

        i.string = parse_ins_to_string(ins, args)

        self.output.append(i)
        self.cur_addr += i.length

    def handle_fixups(self) -> None:
        for ins in self.output:
            if ins.fixup_type == FIXUP_TYPE.NONE:
                # no fixup needed
                continue
            if self.verbose: print("handle fixup for %s" % str(ins))

            sym = ins.fixup_sym
            if sym is None:
                raise Codegen_Exception("fixup: instruction/data has no symbol reference")

            if ins.fixup_type == FIXUP_TYPE.SHORT_BRANCH:
                if not sym.resolved:
                    raise Codegen_Exception("fixup: short branch referring to unresolved symbol '%s'" % sym.name)

                # make sure we're dealing with an instruction
                if not isinstance(ins, Instruction):
                    raise Codegen_Exception("fixup: expected instruction for short branch, got %s" % str(ins))

                # compute the distance
                offset = sym.addr - (ins.addr + 1)
                if offset >= 256 or offset < -256:
                    raise Codegen_Exception("fixup: short branch with too large offset %d" % offset)

                # patch the instruction
                ins.op |= (offset & 0x3ff)
            elif ins.fixup_type == FIXUP_TYPE.LONG_BRANCH:
                if not sym.resolved:
                    raise Codegen_Exception("fixup; long branch referring to unresolved symbol '%s'" % sym.name)

                # make sure we're dealing with an instruction
                if not isinstance(ins, Instruction):
                    raise Codegen_Exception("fixup: expected instruction for long branch, got %s" % str(ins))

                # XXX check the range here

                # compute the distance
                offset = sym.addr - (ins.addr + 2)

                # patch the instruction
                ins.op2 = offset & 0xffff
            elif ins.fixup_type == FIXUP_TYPE.SYMBOL_LONG:
                if not sym.resolved:
                    raise Codegen_Exception("fixup; instruction referring to unresolved symbol '%s'" % sym.name)

                # make sure we're dealing with an instruction
                if not isinstance(ins, Instruction):
                    raise Codegen_Exception("fixup: expected instruction for symbol reference, got %s" % str(ins))

                # patch the instruction
                ins.op2 = sym.addr & 0xffff
            elif ins.fixup_type == FIXUP_TYPE.DATA_SYMBOL_LONG:
                if not sym.resolved:
                    raise Codegen_Exception("fixup; data referring to unresolved symbol '%s'" % sym.name)

                # make sure we're dealing with a data reference
                if not isinstance(ins, Data):
                    raise Codegen_Exception("fixup: expected data reference, got %s" % str(ins))

                # patch the data reference
                ins.data.append(sym.addr)

    def dump_output(self):
        for out in self.output:
            print(out)

    def dump_symbols(self):
        for sym in self.symbols:
            print(self.symbols[sym])

    def output_hex(self, hexfile):
        for out in self.output:
            out.write_hex(hexfile)

    def output_hex2(self, hexfile):
        for out in self.output:
            out.write_hex2(hexfile)

    def output_binary(self, binfile):
        for out in self.output:
            out.write_bin(binfile)

# vim: ts=4 sw=4 expandtab:
