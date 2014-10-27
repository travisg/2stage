
# general class of instruction
ITYPE_ALU = 1
ITYPE_SHORT_BRANCH = 2
ITYPE_SHORT_OR_LONG_BRANCH = 3
ITYPE_LONG_BRANCH = 4

# argument types
ATYPE_NONE      = 1  # nop
ATYPE_DAB       = 2  # add D, A, B
ATYPE_DB        = 3  # add D, B    --- add D, r0, B
ATYPE_D         = 4  # b   D
ATYPE_DA_MINUS1 = 5  # not D, A    --- xor D, A, #-1
ATYPE_AB        = 6  # tst A, B    --- xor r0, A, B

class IFormat:
    def __init__(self, opcode, itype, atype):
        self.opcode = opcode
        self.itype = itype
        self.atype = atype

opcode_table = {
    'add': IFormat(0x0000, ITYPE_ALU, ATYPE_DAB),
    'sub': IFormat(0x1000, ITYPE_ALU, ATYPE_DAB),
    'and': IFormat(0x2000, ITYPE_ALU, ATYPE_DAB),
    'or':  IFormat(0x3000, ITYPE_ALU, ATYPE_DAB),
    'xor': IFormat(0x4000, ITYPE_ALU, ATYPE_DAB),
    'lsl': IFormat(0x5000, ITYPE_ALU, ATYPE_DAB),
    'lsr': IFormat(0x6000, ITYPE_ALU, ATYPE_DAB),
    'asr': IFormat(0x7000, ITYPE_ALU, ATYPE_DAB),

    'beq': IFormat(0x8000 | (0 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bne': IFormat(0x8000 | (1 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bcs': IFormat(0x8000 | (2 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bhs': IFormat(0x8000 | (2 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bcc': IFormat(0x8000 | (3 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'blo': IFormat(0x8000 | (3 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bmi': IFormat(0x8000 | (4 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bpl': IFormat(0x8000 | (5 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bvs': IFormat(0x8000 | (6 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bvc': IFormat(0x8000 | (7 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bhi': IFormat(0x8000 | (8 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bls': IFormat(0x8000 | (9 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bge': IFormat(0x8000 | (10 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'blt': IFormat(0x8000 | (11 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'bgt': IFormat(0x8000 | (12 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'ble': IFormat(0x8000 | (13 << 10), ITYPE_SHORT_BRANCH, ATYPE_D),
    'b':   IFormat(0x8000 | (14 << 10), ITYPE_SHORT_OR_LONG_BRANCH, ATYPE_D),
    'bl':  IFormat(0xb000 | (14 << 10) | (1<<9), ITYPE_LONG_BRANCH, ATYPE_D),

    'nop': IFormat(0x0000, ITYPE_ALU, ATYPE_NONE), # add

    'mov': IFormat(0x0000, ITYPE_ALU, ATYPE_DB), # add
    'neg': IFormat(0x1000, ITYPE_ALU, ATYPE_DB), # sub
    'not': IFormat(0x4000, ITYPE_ALU, ATYPE_DA_MINUS1), # xor
    'teq': IFormat(0x4000, ITYPE_ALU, ATYPE_AB), # xor
    'tst': IFormat(0x2000, ITYPE_ALU, ATYPE_AB), # and
    'cmp': IFormat(0x1000, ITYPE_ALU, ATYPE_AB), # sub
    'cmn': IFormat(0x0000, ITYPE_ALU, ATYPE_AB), # add
}

FIXUP_TYPE_NONE = 0
FIXUP_TYPE_SHORT_BRANCH = 1
FIXUP_TYPE_LONG_BRANCH = 2

class Instruction:
    op = 0
    op2 = 0
    op_length = 1
    addr = 0
    string = ""
    fixup_type = FIXUP_TYPE_NONE
    fixup_sym = None

    def __str__(self):
        return "Instruction op 0x%004x 0x%04x, address 0x%04x '%s' fixup type %d sym: %s" % (
                self.op, self.op2, self.addr, self.string, self.fixup_type, str(self.fixup_sym))

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
        return "r%u" % t[1]
    elif t[0] == 'REGISTER_INDIRECT':
        return "[r%u]" % t[1]
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
    instructions = []
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
        i.op_length = 1

        arg_count = len(ins) - 1

        # switch based on type
        if (op.itype == ITYPE_ALU):
            # handle the up to 3 args of the instruction
            dest_arg = ('REGISTER', 0)
            a_arg = ('REGISTER', 0)
            b_arg = ('REGISTER', 0)

            # match args based on instruction atype
            match = False
            if op.atype == ATYPE_NONE:
                #ATYPE_NONE - nop
                if arg_count == 0:
                    match = True
            elif op.atype == ATYPE_DAB:
                #ATYPE_DAB - add D, A, B
                if arg_count == 3:
                    dest_arg = ins[1]
                    a_arg = ins[2]
                    b_arg = ins[3]
                    match = True
                elif arg_count == 2:    # add D, D, B
                    dest_arg = ins[1]
                    a_arg = ins[1]

                    # if dest is [reg], then have the A source be just reg
                    if a_arg[0] == 'REGISTER_INDIRECT':
                        a_arg = ('REGISTER', a_arg[1])
                    b_arg = ins[2]
                    match = True
                elif arg_count == 1:    # add D, D, D
                    dest_arg = ins[1]
                    a_arg = ins[1]

                    # if dest is [reg], then have the A source be just reg
                    if a_arg[0] == 'REGISTER_INDIRECT':
                        a_arg = ('REGISTER', a_arg[1])
                    b_arg = ins[1]

                    # if dest is [reg], then have the B source be just reg
                    if b_arg[0] == 'REGISTER_INDIRECT':
                        b_arg = ('REGISTER', b_arg[1])
                    match = True
            elif op.atype == ATYPE_DB:
                #ATYPE_DB - add D, B    --- add D, r0, B
                if arg_count == 2:
                    dest_arg = ins[1]
                    b_arg = ins[2]
                    match = True
                elif arg_count == 1:
                    dest_arg = ins[1]
                    b_arg = ins[1]
                    match = True
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
                elif arg_count == 2:
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
                elif arg_count == 2:
                    a_arg = ins[1]
                    b_arg = ins[1]
                    match = True

            if not match:
                raise Codegen_Exception("add_instruction: failed to match atype")

            # construct the instruction out of the ops
            # destination has to be a register or indirect register
            if dest_arg[0] == 'REGISTER':
                i.op |= (0 << 11) | dest_arg[1] << 8
            elif dest_arg[0] == 'REGISTER_INDIRECT':
                i.op |= (1 << 11) | dest_arg[1] << 8
            else:
                raise Codegen_Exception("add_instruction: dest is bogus type '%s'" % str(dest_arg))

            # a arg can only be register
            if a_arg[0] == 'REGISTER':
                i.op |= a_arg[1] << 5
            else:
                raise Codegen_Exception("add_instruction: a is bogus type '%s'" % str(a_arg))

            # b arg can be any type
            if b_arg[0] == 'REGISTER':
                i.op |= (2 << 3) | b_arg[1]
            elif b_arg[0] == 'REGISTER_INDIRECT':
                i.op |= (3 << 3) | b_arg[1]
            elif b_arg[0] == 'NUMBER':
                num = int(b_arg[1])

                # see if we can fit it in a 4 bit signed immediate
                if num < 8 and num > -7:
                    # we can use 4 bit immediate
                    i.op |= (0 << 4) | (num & 0xf)
                elif num < 65536 and num >= -32768:
                    # going to have to use a full 16 bit immediate
                    i.op |= (1 << 4)
                    i.op2 = num & 0xffff
                    i.op_length = 2
                else:
                    raise Codegen_Exception("add_instruction: immediate out of range %d" % int(num))
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
                    i.op_length += 1
                elif arg[0] == 'ID':
                    # 16 bit long address, target is unresolved
                    i.op2 = 0;
                    i.op_length += 1
                    i.fixup_type = FIXUP_TYPE_LONG_BRANCH;
                    i.fixup_sym = self.get_symbol_ref(arg[1])
                    pass
        else:
            raise Codegen_Exception("add_instruction: unhandled ITYPE")

        i.string = parse_ins_to_string(ins)

        self.instructions.append(i)
        self.cur_addr += i.op_length

    def handle_fixups(self):
        for ins in self.instructions:
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

                # compute the distance
                offset = sym.addr - (ins.addr + 2)

                # patch the instruction
                ins.op2 = offset & 0xffff

    def dump_instructions(self):
        for ins in self.instructions:
            print ins
    def dump_symbols(self):
        for sym in self.symbols:
            print self.symbols[sym]

    def output_hex(self, hexfile):
        for ins in self.instructions:
            hexfile.write("%04x // 0x%04x %s\n" % (ins.op, ins.addr, ins.string))
            if ins.op_length == 2:
                hexfile.write("%04x\n"  % (ins.op2))

    def output_binary(self, binfile):
        print "output_binary: UNIMPLEMENTED!"
        pass

# vim: ts=4 sw=4 expandtab:
