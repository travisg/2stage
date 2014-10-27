#!/usr/bin/env python

import sys
import argparse
import lexparse
import subprocess
import codegen

def main():

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
    parser.add_argument('-o','--out', nargs=1, type=argparse.FileType('w', 0), help="output binary")
    parser.add_argument('-x','--hex', nargs=1, type=argparse.FileType('w', 0), help="output hex file")
    parser.add_argument('-v','--verbose', action='store_true', default=False)

    args = parser.parse_args()
    #print args

    code = codegen.Codegen()
    lexparse.codegen = code

    # preprocess the assembly
    cpp = subprocess.Popen(['cpp','-nostdinc'], stdin=args.infile, stdout=subprocess.PIPE)

    if args.verbose: print "starting parser"

    for line in cpp.stdout:
        if args.verbose: print "parsing line: ", line,
        lexparse.yacc.parse(line,debug=False)

    if args.verbose: print "processing fixups"

    code.handle_fixups()

    if args.verbose:
        print "dumping instructions:"
        code.dump_instructions()
        print "dumping symbols:"
        code.dump_symbols()

    if args.hex != None:
        if args.verbose: print "outputting hex file"
        code.output_hex(args.hex[0])
        args.hex[0].close()

    if args.out != None:
        if args.verbose: print "outputting binary"
        code.output_binary(args.out[0])
        args.out[0].close()

if __name__ == "__main__":
    main()

# vim: ts=4 sw=4 expandtab:
