
# general class of instruction
ITYPE_ALU = 1
ITYPE_BRANCH = 2
ITYPE_BRANCH_OR_ALU = 3

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

    'beq': IFormat(0x8000 | (0 << 10), ITYPE_BRANCH, ATYPE_D),
    'bne': IFormat(0x8000 | (1 << 10), ITYPE_BRANCH, ATYPE_D),
    'bcs': IFormat(0x8000 | (2 << 10), ITYPE_BRANCH, ATYPE_D),
    'bhs': IFormat(0x8000 | (2 << 10), ITYPE_BRANCH, ATYPE_D),
    'bcc': IFormat(0x8000 | (3 << 10), ITYPE_BRANCH, ATYPE_D),
    'blo': IFormat(0x8000 | (3 << 10), ITYPE_BRANCH, ATYPE_D),
    'bmi': IFormat(0x8000 | (4 << 10), ITYPE_BRANCH, ATYPE_D),
    'bpl': IFormat(0x8000 | (5 << 10), ITYPE_BRANCH, ATYPE_D),
    'bvs': IFormat(0x8000 | (6 << 10), ITYPE_BRANCH, ATYPE_D),
    'bvc': IFormat(0x8000 | (7 << 10), ITYPE_BRANCH, ATYPE_D),
    'bhi': IFormat(0x8000 | (8 << 10), ITYPE_BRANCH, ATYPE_D),
    'bls': IFormat(0x8000 | (9 << 10), ITYPE_BRANCH, ATYPE_D),
    'bge': IFormat(0x8000 | (10 << 10), ITYPE_BRANCH, ATYPE_D),
    'blt': IFormat(0x8000 | (11 << 10), ITYPE_BRANCH, ATYPE_D),
    'bgt': IFormat(0x8000 | (12 << 10), ITYPE_BRANCH, ATYPE_D),
    'ble': IFormat(0x8000 | (13 << 10), ITYPE_BRANCH, ATYPE_D),
    'b':   IFormat(0x8000 | (15 << 10), ITYPE_BRANCH_OR_ALU, ATYPE_D),

    'nop': IFormat(0x0000, ITYPE_ALU, ATYPE_NONE), # add

    'mov': IFormat(0x0000, ITYPE_ALU, ATYPE_DB), # add
    'neg': IFormat(0x1000, ITYPE_ALU, ATYPE_DB), # sub
    'not': IFormat(0x4000, ITYPE_ALU, ATYPE_DA_MINUS1), # xor
    'teq': IFormat(0x4000, ITYPE_ALU, ATYPE_AB), # xor
    'tst': IFormat(0x2000, ITYPE_ALU, ATYPE_AB), # and
    'cmp': IFormat(0x1000, ITYPE_ALU, ATYPE_AB), # sub
    'cmn': IFormat(0x0000, ITYPE_ALU, ATYPE_AB), # add
}

class Instruction:
    def __init__(self):
        self.op = 0
        self.op2 = 0
        self.op_length = 1
        self.addr = 0
        self.string = ""
        return

    def __str__(self):
        return "Instruction op 0x%004x 0x%04x, address 0x%04x '%s'" % (self.op, self.op2, self.addr, self.string)

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
    def __init__(self):
        self.addr = 0
        self.instructions = []
        print "codegen new"

    def add_label(self, ins):
        print "add label %s, address %#x" % (str(ins), self.addr)

    def add_directive(self, ins):
        print "add directive %s" % str(ins)


    def add_instruction(self, ins):
        print "add instruction %s" % str(ins)

        i = Instruction()
        i.addr = self.addr

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
            elif op.atype & ATYPE_DAB:
                #ATYPE_DAB - add D, A, B
                if arg_count == 3:
                    dest_arg = ins[1]
                    a_arg = ins[2]
                    b_arg = ins[3]
                    match = True
                elif arg_count == 2:    # add D, r0, B
                    dest_arg = ins[1]
                    b_arg = ins[2]
                    match = True
                elif arg_count == 1:    # add D, r0, D
                    dest_arg = ins[1]
                    b_arg = ins[1]
                    match = True
            elif op.atype & ATYPE_DB:
                #ATYPE_DB - add D, B    --- add D, r0, B
                if arg_count == 2:
                    dest_arg = ins[1]
                    b_arg = ins[2]
                    match = True
                elif arg_count == 1:
                    dest_arg = ins[1]
                    b_arg = ins[1]
                    match = True
            elif op.atype & ATYPE_D:
                #ATYPE_D - b   D
                if arg_count == 1:
                    dest_arg = ins[1]
                    match = True
            elif op.atype & ATYPE_DA_MINUS1:
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
            elif op.atype & ATYPE_AB:
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
                raise Codegen_Exception("add_instruction: dest is bogus type '%s'" % dest_arg)

            # a arg can only be register
            if a_arg[0] == 'REGISTER':
                i.op |= a_arg[1] << 5
            else:
                raise Codegen_Exception("add_instruction: a is bogus type '%s'" % a_arg)

            # b arg can be any type
            if b_arg[0] == 'REGISTER':
                i.op |= (2 << 3) | b_arg[1]
            elif b_arg[0] == 'REGISTER_INDIRECT':
                i.op |= (3 << 3) | b_arg[1]
            elif b_arg[0] == 'NUMBER':
                num = int(b_arg[1])
                print "num %d" % b_arg[1]

                # see if we can fit it in a 4 bit signed immediate
                if num < 8 and num > -7:
                    # we can use 4 bit immediate
                    i.op |= (0 << 4) | (num & 0xf)
                elif num < 32768 and num > -32767:
                    # going to have to use a full 16 bit immediate
                    i.op |= (1 << 4)
                    i.op2 = num & 0xffff
                    i.op_length = 2
                    self.addr += 1
                else:
                    raise Codegen_Exception("add_instruction: immediate out of range %s" % str(num))
            else:
                raise Codegen_Exception("add_instruction: b is bogus type '%s'" % b_arg)
        elif op.itype == ITYPE_BRANCH or op.itype == ITYPE_BRANCH_OR_ALU:
            # handle branches

            

            pass
        else:
            raise Codegen_Exception("add_instruction: unhandled ITYPE")

        i.string = parse_ins_to_string(ins)

        self.instructions.append(i)
        self.addr += 1

    def dump_instructions(self):
        for ins in self.instructions:
            print ins

# vim: ts=4 sw=4 expandtab:
