#!/usr/bin/env python

import sys
import lexparse
import codegen

def main():
    infile = sys.stdin

    code = codegen.Codegen()
    lexparse.codegen = code

    print "starting parser"
    for line in infile:
        lexparse.yacc.parse(line,debug=False)

    print "dumping instructions:"
    code.dump_instructions()

if __name__ == "__main__":
    main()

# vim: ts=4 sw=4 expandtab:
