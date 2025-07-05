#!/usr/bin/env python3

import sys
import argparse
import lexparse
import subprocess
import codegen

def main():

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
    parser.add_argument('-o','--out', nargs=1, type=argparse.FileType('wb', 0), help="output binary")
    parser.add_argument('-x','--hex', nargs=1, type=argparse.FileType('wt', 1), help="output hex file")
    parser.add_argument('-X','--hex2', nargs=1, type=argparse.FileType('wt', 1), help="output hex file, alternate format")
    parser.add_argument('-v','--verbose', action='count', default=0, help="verbose output")

    args = parser.parse_args()
    #print(args)

    code = codegen.Codegen()
    lexparse.gen = code
    code.verbose = True if args.verbose > 1 else False

    # preprocess the assembly
    if args.verbose > 0: print("starting preprocessor")
    cpp = subprocess.Popen(['cpp','-nostdinc'], stdin=args.infile, stdout=subprocess.PIPE, text=True)

    # read in the preprocessed assembly and parse it
    if args.verbose > 0: print("starting parser")
    for line in cpp.stdout: # type: ignore
        if args.verbose > 1: print("parsing line: ", line, end='')
        lexparse.yacc.parse(line, debug=False)

    if args.verbose > 0: print("processing fixups")
    code.handle_fixups()

    if args.verbose > 0:
        print("dumping instructions/data:")
        code.dump_output()
        print("dumping symbols:")
        code.dump_symbols()

    if args.hex is not None:
        if args.verbose > 0: print("outputting hex file")
        code.output_hex(args.hex[0])
        args.hex[0].close()

    if args.hex2 is not None:
        if args.verbose > 0: print("outputting hex file, alternate format")
        code.output_hex2(args.hex2[0])
        args.hex2[0].close()

    if args.out is not None:
        if args.verbose > 0: print("outputting binary")
        code.output_binary(args.out[0])
        args.out[0].close()

if __name__ == "__main__":
    main()

# vim: ts=4 sw=4 expandtab:
