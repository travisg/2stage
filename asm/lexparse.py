
codegen = None

# lexer
tokens = (
    'NUM',
    'REGISTER',
    'DIRECTIVE',
    'ID',
    'STRING',
    'INSTRUCTION',
)

INSTRUCTIONS = (
    "mov",
    "add",
    "adc",
    "sub",
    "sbc",
    "and",
    "or",
    "xor",
    "lsl",
    "lsr",
    "asr",
    "ror",
    "b",
    "bl",

    # load/store
    "ldr",
    "str",

    # different branches
    "beq",
    "bne",
    "bcs", "bhs",
    "bcc", "blo",
    "bmi",
    "bpl",
    "bvs",
    "bvc",
    "bhi",
    "bls",
    "bge",
    "blt",
    "bgt",
    "ble",

    # pseudo instructions
    "nop",
    "mov",
    "neg",
    "not",
    "teq",
    "tst",
    "cmp",
    "cmn",
)

t_ignore_COMMENT = r';.*|//.*'
t_ignore = ' \t'

literals = ':;,[]#'

class LexerError:
    pass

def t_DIRECTIVE(t):
    r'\.\w+'
    #print "directive %s" % t
    return t

def t_HEXNUM(t):
    r'0[xX][A-Fa-f0-9]+'
    t.value = ('NUMBER', int(t.value[2:], 16))
    #print "hexnum %s" % t
    t.type = 'NUM'
    return t

def t_NUM(t):
    r'-?\d+'
    t.value = ('NUMBER', int(t.value))
    #print "num %s" % t
    return t

def t_REGISTER(t):
    r'[rR]\d|sp|lr|pc|cr'

    if t.value == 'lr':
        t.value = ('REGISTER', 8);
    elif t.value == 'sp':
        t.value = ('REGISTER', 9);
    elif t.value == 'pc':
        t.value = ('REGISTER', 10);
    elif t.value == 'cr':
        t.value = ('REGISTER', 11);
    else:
        t.value = ('REGISTER', int(t.value[1:2]))
        if (t.value[1] >= 8):
            raise LexerError

    #print "register %s" % t
    return t

def t_ID(t):
    r'[A-Za-z_]\w*'

    if t.value in INSTRUCTIONS:
        t.type = 'INSTRUCTION'
    else:
        t.value = ('ID', t.value)

    #print "id %s" % t
    return t

def t_STRING(t):
    r'("(\\"|[^"])*")|(\'(\\\'|[^\'])*\')'
    t.value = t.value.strip('"\'')
    #print "string %s" % t
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    #print "line %d" % t.lexer.lineno

def t_error(t):
    print "lexer error %s at line %u" % (t, t.lineno)
    raise LexerError

import ply.lex as lex
lex.lex(debug=False)

# parser
def p_expr(p):
    '''expr         : label
                    | instruction
                    | directive
                    | preprocessor_directive
                    '''
    #print "parser expr %s %s" % (p, p[0])

def p_label(p):
    '''label        : ID ':' '''
    #print "parser label %s, line %d" % (str(p[1]), p.lineno(1))
    codegen.add_label(p[1])

def p_instruction(p):
    '''instruction  : instruction_3addr
                    | instruction_2addr
                    | instruction_1addr
                    | instruction_0addr'''

def p_instruction_3addr(p):
    '''instruction_3addr    : INSTRUCTION REGISTER ',' REGISTER ',' REGISTER
                            | INSTRUCTION REGISTER ',' REGISTER ',' NUM
                            | INSTRUCTION REGISTER ',' REGISTER ',' ID'''
    #print "parser instruction 3addr %s" % p[1]
    codegen.add_instruction((p[1], p[2], p[4], p[6]))

def p_instruction_2addr(p):
    '''instruction_2addr    : INSTRUCTION REGISTER ',' NUM
                            | INSTRUCTION REGISTER ',' REGISTER
                            | INSTRUCTION REGISTER ',' ID'''
    #print "parser instruction 2addr %s" % p[1]
    codegen.add_instruction((p[1], p[2], p[4]))

def p_instruction_1addr(p):
    '''instruction_1addr    : INSTRUCTION REGISTER
                            | INSTRUCTION NUM
                            | INSTRUCTION ID'''
    #print "parser instruction 1addr %s" % p[1]
    codegen.add_instruction((p[1], p[2]))

def p_instruction_0addr(p):
    '''instruction_0addr    : INSTRUCTION'''
    #print "parser instruction 0addr %s" % p[1]
    codegen.add_instruction((p[1], ))

def p_directive(p):
    '''directive            : DIRECTIVE
                            | DIRECTIVE ID
                            | DIRECTIVE STRING
                            | DIRECTIVE NUM'''
    #print "parser directive %s" % p[1]
    if len(p) == 3:
        codegen.add_directive((p[1], p[2]))
    else:
        codegen.add_directive((p[1], ))

def p_preprocessor_directive(p):
    '''preprocessor_directive : '#' NUM STRING
                            | '#' NUM STRING NUM
                            | '#' NUM STRING NUM NUM
                            | '#' NUM STRING NUM NUM NUM
                            | '#' NUM STRING NUM NUM NUM NUM'''
    #print "parser preprocessor_directive, %s line %d" % (p[2], p.lineno(2))

    # set the lineno to the number
    p.lexer.lineno = int(p[2][1])

#def p_emtpy(p):
    #'empty : '
    #pass

class ParseError:
    pass

def p_error(p):
    if p != None:
        print "parser error %s on line %u" % (str(p.value), p.lineno)
        raise ParseError

import ply.yacc as yacc
yacc.yacc()

# vim: ts=4 sw=4 expandtab:

