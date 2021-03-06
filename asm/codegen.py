import array
import struct

# general class of instruction
ITYPE_ALU = 1
ITYPE_SHORT_BRANCH = 2
ITYPE_SHORT_OR_LONG_BRANCH = 3
ITYPE_LONG_BRANCH = 4

# argument types
ATYPE_NONE      = 1  # nop
ATYPE_DAB       = 2  # add D, A, B
ATYPE_DAB_LS    = 3  # ldr r0, r1, r2
ATYPE_DB        = 4  # add D, B    --- add D, r0, B
ATYPE_D         = 5  # b   D
ATYPE_DA_MINUS1 = 6  # not D, A    --- xor D, A, #-1
ATYPE_AB        = 7  # tst A, B    --- xor r0, A, B

class IFormat:
    def __init__(self, opcode, itype, atype):
        self.opcode = opcode
        self.itype = itype
        self.atype = atype

opcode_table = {
    'mov': IFormat(0b00000 << 11, ITYPE_ALU, ATYPE_DB),
    'add': IFormat(0b00001 << 11, ITYPE_ALU, ATYPE_DAB),
    'adc': IFormat(0b00010 << 11, ITYPE_ALU, ATYPE_DAB),
    'sub': IFormat(0b00011 << 11, ITYPE_ALU, ATYPE_DAB),
    'sbc': IFormat(0b00100 << 11, ITYPE_ALU, ATYPE_DAB),
    'and': IFormat(0b00101 << 11, ITYPE_ALU, ATYPE_DAB),
    'or':  IFormat(0b00110 << 11, ITYPE_ALU, ATYPE_DAB),
    'xor': IFormat(0b00111 << 11, ITYPE_ALU, ATYPE_DAB),
    'lsl': IFormat(0b01000 << 11, ITYPE_ALU, ATYPE_DAB),
    'lsr': IFormat(0b01001 << 11, ITYPE_ALU, ATYPE_DAB),
    'asr': IFormat(0b01010 << 11, ITYPE_ALU, ATYPE_DAB),
    'ror': IFormat(0b01011 << 11, ITYPE_ALU, ATYPE_DAB),

    'ldr': IFormat(0b01100 << 11, ITYPE_ALU, ATYPE_DAB_LS),
    'str': IFormat(0b01101 << 11, ITYPE_ALU, ATYPE_DAB_LS),

  #'push': IFormat(0b01110 << 11, ITYPE_ALU, ATYPE_DAB),
   #'pop': IFormat(0b01111 << 11, ITYPE_ALU, ATYPE_DAB),

    'beq': IFormat(0b10000 << 11 | (0b0000 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bne': IFormat(0b10000 << 11 | (0b0001 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bcs': IFormat(0b10000 << 11 | (0b0010 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bhs': IFormat(0b10000 << 11 | (0b0010 << 10), ITYPE_SHORT_BRANCH, ATYPE_D), # same as bcs
    'bcc': IFormat(0b10000 << 11 | (0b0011 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'blo': IFormat(0b10000 << 11 | (0b0011 << 10), ITYPE_SHORT_BRANCH, ATYPE_D), # same as bcc
    'bmi': IFormat(0b10000 << 11 | (0b0100 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bpl': IFormat(0b10000 << 11 | (0b0101 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bvs': IFormat(0b10000 << 11 | (0b0110 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bvc': IFormat(0b10000 << 11 | (0b0111 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bhi': IFormat(0b10000 << 11 | (0b1000 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bls': IFormat(0b10000 << 11 | (0b1001 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bge': IFormat(0b10000 << 11 | (0b1010 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'blt': IFormat(0b10000 << 11 | (0b1011 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bgt': IFormat(0b10000 << 11 | (0b1100 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'ble': IFormat(0b10000 << 11 | (0b1101 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'b':   IFormat(0b10000 << 11 | (0b1110 << 10), ITYPE_SHORT_OR_LONG_BRANCH, ATYPE_D),
    'bl':  IFormat(0b10000 << 11 | (0b1110 << 10) | (1<<9), ITYPE_LONG_BRANCH, ATYPE_D),

    'nop': IFormat(0b00000 << 11, ITYPE_ALU, ATYPE_NONE), # mov r0, r0

    'neg': IFormat(0b00011 << 11, ITYPE_ALU, ATYPE_DB), # sub d, r0, b
    'not': IFormat(0b00111 << 11, ITYPE_ALU, ATYPE_DA_MINUS1), # xor d, a, #-1
    'teq': IFormat(0b00111 << 11, ITYPE_ALU, ATYPE_AB), # xor r0, a, b
    'tst': IFormat(0b00101 << 11, ITYPE_ALU, ATYPE_AB), # and r0, a, b
    'cmp': IFormat(0b00011 << 11, ITYPE_ALU, ATYPE_AB), # sub r0, a, b
    'cmn': IFormat(0b00001 << 11, ITYPE_ALU, ATYPE_AB), # add r0, a, b
}

FIXUP_TYPE_NONE = 0
FIXUP_TYPE_SHORT_BRANCH = 1
FIXUP_TYPE_LONG_BRANCH = 2
FIXUP_TYPE_SYMBOL_LONG = 3
FIXUP_TYPE_DATA_SYMBOL_LONG = 4

class OutputData:
    addr = 0
    length = 0
    string = ""
    fixup_type = FIXUP_TYPE_NONE
    fixup_sym = None

class Instruction(OutputData):
    op = 0
    op2 = 0

    def write_hex(self, outfile):
        outfile.write("%04x // 0x%04x %s\n" % (self.op, self.addr, self.string))
        if self.length == 2:
            outfile.write("%04x\n"  % (self.op2))

    def write_hex2(self, outfile):
        outfile.write("0x%04x, // 0x%04x %s\n" % (self.op, self.addr, self.string))
        if self.length == 2:
            outfile.write("0x%04x,\n"  % (self.op2))

    def write_bin(self, outfile):
        outfile.write(struct.pack('>H', self.op))
        if self.length == 2:
            outfile.write(struct.pack('>H', self.op2))

    def __str__(self):
        return "Instruction op 0x%004x 0x%04x, address 0x%04x '%s' fixup type %d sym: %s" % (
                self.op, self.op2, self.addr, self.string, self.fixup_type, str(self.fixup_sym))

class Data(OutputData):
    data = None

    def __init__(self):
        self.data = array.array('H')

    def write_hex(self, outfile):
        for i in range(self.length):
            if i == 0:
                outfile.write("%04x // 0x%04x %s\n" % (self.data[i], self.addr, self.string))
            else:
                outfile.write("%04x\n" % self.data[i])

    def write_hex2(self, outfile):
        for i in range(self.length):
            if i == 0:
                outfile.write("0x%04x, // 0x%04x %s\n" % (self.data[i], self.addr, self.string))
            else:
                outfile.write("0x%04x,\n" % self.data[i])

    def write_bin(self, outfile):
        for i in range(self.length):
            outfile.write(struct.pack('>H', self.data[i]))

    def __str__(self):
        return "Data '%s', address 0x%04x '%s' fixup type %d sym: %s" % (
                self.data, self.addr, self.string, self.fixup_type, str(self.fixup_sym))

class Symbol:
    name = ""
    addr = 0
    resolved = False
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Symbol '%s' at addr 0x%04x resolved %d" % (self.name, self.addr, self.resolved)

class Codegen_Exception:
    def __init__(self, string):
        self.string = string

    def __str__(self):
        return self.string

def parse_tuple_to_string(t):
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

def parse_ins_to_string(ins):
    if len(ins) == 1:
        return "%s" % str(ins[0])
    elif len(ins) == 2:
        return "%s %s" % (str(ins[0]),
            parse_tuple_to_string(ins[1]))
    elif len(ins) == 3:
        return "%s %s, %s" % (str(ins[0]),
            parse_tuple_to_string(ins[1]),
            parse_tuple_to_string(ins[2]))
    elif len(ins) == 4:
        return "%s %s, %s, %s" % (str(ins[0]),
            parse_tuple_to_string(ins[1]),
            parse_tuple_to_string(ins[2]),
            parse_tuple_to_string(ins[3]))
    return "unk"

class Codegen:
    cur_addr = 0
    output = []
    symbols = {}
    verbose = False

    def __init__(self):
        pass

    def add_label(self, label):
        label = str(label[1])
        if self.verbose: print "add label %s, address %#x" % (label, self.cur_addr)

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
    def get_symbol_ref(self, label):
        try:
            sym = self.symbols[label]
            return sym
        except:
            # previously unseen symbol
            sym = Symbol(label)
            self.symbols[label] = sym
            return sym

    def add_directive(self, ins):
        if self.verbose: print "add directive %s" % str(ins)
        if ins[0] == ".word":
            d = Data()
            d.addr = self.cur_addr
            d.length = 1
            if ins[1][0] == 'NUMBER':
                num = int(ins[1][1])
                d.string = ".word %04x" % num
                d.data.append(num)
            elif ins[1][0] == 'ID':
                # 16 bit long address, target is unresolved
                d.fixup_type = FIXUP_TYPE_DATA_SYMBOL_LONG;
                d.fixup_sym = self.get_symbol_ref(ins[1][1])
                d.string = ".word %s" % ins[1][1]
            self.output.append(d)
            self.cur_addr += d.length
        elif ins[0] in { ".ascii", ".asciiz" }:
            if type(ins[1]) is not str:
                raise Codegen_Exception("add_directive: .ascii used without string")

            d = Data()
            d.string = "%s '%s'" % (ins[0], ins[1])
            d.addr = self.cur_addr

            for c in ins[1]:
                d.data.append(ord(c))
            if ins[0] == ".asciiz":
                d.data.append(0)

            d.length = len(d.data)

            self.output.append(d)
            self.cur_addr += d.length
        elif ins[0] in { ".asciib", ".asciibz" }:
            if type(ins[1]) is not str:
                raise Codegen_Exception("add_directive: .asciib used without string")

            # null terminate and make sure string length is a multiple of 2
            s = ins[1]
            if ins[0] == ".asciibz":
                s += '\0'
            if len(s) % 2:
                s += '\0'

            d = Data()
            d.addr = self.cur_addr
            d.data.fromstring(s)
            d.string = "%s '%s'" % (ins[0], ins[1])
            d.length = len(d.data)

            self.output.append(d)
            self.cur_addr += d.length
        else:
            raise Codegen_Exception("add_directive: unknown directive '%s'" % ins[0])

    def add_instruction(self, ins):
        if self.verbose: print "add instruction %s" % str(ins)

        i = Instruction()
        i.addr = self.cur_addr

        # lookup the opcode
        op = 0
        try:
            op = opcode_table[ins[0]]
        except:
            raise Codegen_Exception("add_instruction: unknown instruction '%s'" % ins[0])

        i.op = op.opcode
        i.length = 1

        arg_count = len(ins) - 1

        # switch based on type
        if (op.itype == ITYPE_ALU):
            # set the default args
            dest_arg = ('REGISTER', 0)
            a_arg = ('REGISTER', 0)
            b_arg = ('NUMBER', 0)

            # match args based on instruction atype
            match = False
            if op.atype == ATYPE_NONE:
                #ATYPE_NONE - nop
                if arg_count == 0:
                    match = True
            elif op.atype == ATYPE_DAB:
                if arg_count == 3:      # add D, A, B
                    dest_arg = ins[1]
                    a_arg = ins[2]
                    b_arg = ins[3]
                    match = True
                elif arg_count == 2:    # add D, D, B
                    dest_arg = ins[1]
                    a_arg = ins[1]
                    b_arg = ins[2]
                    match = True
                elif arg_count == 1:    # add D, D, D
                    dest_arg = ins[1]
                    a_arg = ins[1]
                    b_arg = ins[1]
                    match = True
            elif op.atype == ATYPE_DAB_LS:
                if arg_count == 3:      # ldr D, A, B
                    dest_arg = ins[1]
                    a_arg = ins[2]
                    b_arg = ins[3]
                    match = True
                elif arg_count == 2:    # ldr D, B, r0 or ldr D, r0, IMM
                    dest_arg = ins[1]
                    # if its two arg, assign immediate to B slot, register to A slot
                    if ins[2][0] == 'REGISTER':
                        a_arg = ins[2]
                    else:
                        b_arg = ins[2]
                    match = True
                elif arg_count == 1:    # ldr D, D, r0
                    dest_arg = ins[1]
                    a_arg = ins[1]
                    match = True
            elif op.atype == ATYPE_DB:
                #ATYPE_DB - add D, B    --- add D, r0, B or add D, A, r0
                temp_arg = None
                if arg_count == 2:
                    dest_arg = ins[1]
                    temp_arg = ins[2]
                    match = True
                elif arg_count == 1:
                    dest_arg = ins[1]
                    temp_arg = ins[1]
                    match = True

                # if its regster to register, use the a slot, and assign immediate to b
                if match and temp_arg[0] == 'REGISTER':
                    a_arg = temp_arg
                else:
                    b_arg = temp_arg
            elif op.atype == ATYPE_D:
                #ATYPE_D - b   D
                if arg_count == 1:
                    dest_arg = ins[1]
                    match = True
            elif op.atype == ATYPE_DA_MINUS1:
                #ATYPE_DA_MINUS1 - not D, A    --- xor D, A, #-1
                if arg_count == 2:
                    dest_arg = ins[1]
                    a_arg = ins[2]
                    b_arg = ('NUMBER', -1)
                    match = True
                elif arg_count == 1:
                    dest_arg = ins[1]
                    a_arg = ins[1]
                    b_arg = ('NUMBER', -1)
                    match = True
            elif op.atype == ATYPE_AB:
                #ATYPE_AB - tst A, B    --- xor r0, A, B
                if arg_count == 2:
                    a_arg = ins[1]
                    b_arg = ins[2]
                    match = True
                elif arg_count == 1:
                    a_arg = ins[1]
                    b_arg = ins[1]
                    match = True

            if not match:
                raise Codegen_Exception("add_instruction: failed to match atype")

            d_special = False
            a_special = False

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
                i.fixup_type = FIXUP_TYPE_SYMBOL_LONG;
                i.fixup_sym = self.get_symbol_ref(b_arg[1])

                # if either d or a is special, we'll need to reuse the b field to encode it
                i.op |= (0b11 << 3)
                if a_special: i.op |= (1 << 0)
                if d_special: i.op |= (1 << 1)

                # going to have to use a full 16 bit immediate
                i.op |= (1 << 2)
                i.op2 = 0; # patched later
                i.length = 2
            else:
                raise Codegen_Exception("add_instruction: b is bogus type '%s'" % b_arg)
        elif op.itype == ITYPE_SHORT_BRANCH or op.itype == ITYPE_LONG_BRANCH or op.itype == ITYPE_SHORT_OR_LONG_BRANCH:
            # handle branches
            if arg_count != 1:
                raise Codegen_Exception("add_instruction: invalid number of args for branch")

            arg = ins[1]

            # see what form it is
            long_branch = False
            if op.itype == ITYPE_LONG_BRANCH:
                long_branch = True
            elif op.itype == ITYPE_SHORT_OR_LONG_BRANCH:
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
                    i.op |= (int(arg[1]) & 0x3ff);
                elif arg[0] == 'ID':
                    # short branch, target is unresolved
                    i.fixup_type = FIXUP_TYPE_SHORT_BRANCH;
                    i.fixup_sym = self.get_symbol_ref(arg[1])
            else:
                # long branch
                i.op |= (0xf << 10); # use NV condition

                if arg[0] == 'REGISTER':
                    # its a register branch
                    if (arg[1] == 0):
                        raise Codegen_Exception("add_instruction: cannot generate register branch with r0")
                    i.op |= arg[1];
                elif arg[0] == 'NUMBER':
                    # it's a 16bit signed immediate 2-word branch
                    i.op2 = (arg[1] & 0xffff);
                    i.length += 1
                elif arg[0] == 'ID':
                    # 16 bit long address, target is unresolved
                    i.op2 = 0;
                    i.length += 1
                    i.fixup_type = FIXUP_TYPE_LONG_BRANCH;
                    i.fixup_sym = self.get_symbol_ref(arg[1])
                    pass
        else:
            raise Codegen_Exception("add_instruction: unhandled ITYPE")

        i.string = parse_ins_to_string(ins)

        self.output.append(i)
        self.cur_addr += i.length

    def handle_fixups(self):
        for ins in self.output:
            if ins.fixup_type == FIXUP_TYPE_SHORT_BRANCH:
                sym = ins.fixup_sym
                if not sym.resolved:
                    raise Codegen_Exception("fixup: short branch referring to unresolved symbol '%s'" % sym.name)

                # compute the distance
                offset = sym.addr - (ins.addr + 1)
                if offset >= 256 or offset < -256:
                    raise Codegen_Exception("fixup: short branch with too large offset %d" % offset)

                # patch the instruction
                ins.op |= (offset & 0x3ff)
            elif ins.fixup_type == FIXUP_TYPE_LONG_BRANCH:
                sym = ins.fixup_sym
                if not sym.resolved:
                    raise Codegen_Exception("fixup; long branch referring to unresolved symbol '%s'" % sym.name)

                # XXX check the range here

                # compute the distance
                offset = sym.addr - (ins.addr + 2)

                # patch the instruction
                ins.op2 = offset & 0xffff
            elif ins.fixup_type == FIXUP_TYPE_SYMBOL_LONG:
                sym = ins.fixup_sym
                if not sym.resolved:
                    raise Codegen_Exception("fixup; instruction referring to unresolved symbol '%s'" % sym.name)

                # patch the instruction
                ins.op2 = sym.addr & 0xffff
            elif ins.fixup_type == FIXUP_TYPE_DATA_SYMBOL_LONG:
                sym = ins.fixup_sym
                if not sym.resolved:
                    raise Codegen_Exception("fixup; data referring to unresolved symbol '%s'" % sym.name)

                # patch the data reference
                ins.data.append(sym.addr)

    def dump_output(self):
        for out in self.output:
            print out

    def dump_symbols(self):
        for sym in self.symbols:
            print self.symbols[sym]

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
