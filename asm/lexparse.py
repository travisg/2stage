# vim: ts=4 sw=4 expandtab:

# lexer
tokens = (
    'NUM',
    'REGISTER',
    'DIRECTIVE',
    'ID',
    'STRING',
    'INSTRUCTION'
)

INSTRUCTIONS = (
    "add",
    "sub",
    "and",
    "or",
    "xor",
    "lsl",
    "lsr",
    "asr",
    "b",

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

t_ignore_COMMENT = r';.*|^\#.*'
t_ignore = ' \t'

literals = ':,[]'

def t_DIRECTIVE(t):
    r'\.\w+'
    #print "directive %s" % t
    return t

def t_HEXNUM(t):
    r'\#0[xX][A-Fa-f0-9]+'
    t.value = int(t.value[3:], 16)
    #print "hexnum %s" % t
    t.type = 'NUM'
    return t

def t_NUM(t):
    r'\#-?\d+'
    t.value = int(t.value[1:])
    #print "num %s" % t
    return t

def t_REGISTER(t):
    r'[rR]\d|\[[rR]\d\]|sp|\[sp\]|lr|\[lr\]|pc'

    if t.value == 'sp':
        t.value = 6;
    elif t.value == '[sp]':
        t.value = 6;
        t.indirect = True
    elif t.value == 'lr':
        t.value = 7;
    elif t.value == '[lr]':
        t.value = 7;
        t.indirect = True
    elif t.value == 'pc':
        t.value = 0;
        t.indirect = True
    elif t.value[0] == '[':
        t.value = int(t.value[2:3])
        t.indirect = True
    else:
        t.value = int(t.value[1:2])

    #print "register %s" % t
    return t

def t_ID(t):
    r'[A-Za-z_]\w*'

    if t.value in INSTRUCTIONS:
        t.type = 'INSTRUCTION'

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
    print "lexer error %s" % t

import ply.lex as lex
lex.lex(debug=False)

# parser
def p_expr(p):
    '''expr         : label
                    | instruction
                    | directive
                    '''
    #print "parser expr %s %s" % (p, p[0])

def p_label(p):
    '''label        : ID ':' '''
    print "parser label %s" % p[1]

def p_instruction(p):
    '''instruction  : instruction_3addr
                    | instruction_2addr
                    | instruction_1addr
                    | instruction_0addr'''

def p_instruction_3addr(p):
    '''instruction_3addr    : INSTRUCTION REGISTER ',' REGISTER ',' REGISTER
                            | INSTRUCTION REGISTER ',' REGISTER ',' NUM
                            | INSTRUCTION REGISTER ',' REGISTER ',' ID'''
    print "parser instruction 3addr %s" % p[1]

def p_instruction_2addr(p):
    '''instruction_2addr    : INSTRUCTION REGISTER ',' NUM
                            | INSTRUCTION REGISTER ',' REGISTER
                            | INSTRUCTION REGISTER ',' ID'''
    print "parser instruction 2addr %s" % p[1]

def p_instruction_1addr(p):
    '''instruction_1addr    : INSTRUCTION REGISTER
                            | INSTRUCTION NUM
                            | INSTRUCTION ID'''
    print "parser instruction 1addr %s" % p[1]

def p_instruction_0addr(p):
    '''instruction_0addr    : INSTRUCTION'''
    print "parser instruction 0addr %s" % p[1]

def p_directive(p):
    '''directive            : DIRECTIVE
                            | DIRECTIVE ID
                            | DIRECTIVE STRING
                            | DIRECTIVE NUM'''
    print "parser directive %s" % p[1]

#def p_emtpy(p):
    #'empty : '
    #pass

def p_error(p):
    if p != None:
        print "parser error %s" % p

import ply.yacc as yacc
yacc.yacc()

