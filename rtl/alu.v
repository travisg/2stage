/*
 * Copyright (c) 2014 Travis Geiselbrecht
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files
 * (the "Software"), to deal in the Software without restriction,
 * including without limitation the rights to use, copy, modify, merge,
 * publish, distribute, sublicense, and/or sell copies of the Software,
 * and to permit persons to whom the Software is furnished to do so,
 * subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 * IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
 * CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
 * TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */
`timescale 1ns/1ns

module alu(
    input [2:0] op,

    input [WIDTH-1:0] a,
    input [WIDTH-1:0] b,
    output [WIDTH-1:0] result,

    output [3:0] cc
);

parameter WIDTH = 16;

always_comb begin

    /* do the op */
    case (op)
        3'b000: result = a + b;
        3'b001: result = a - b;
        3'b010: result = a & b;
        3'b011: result = a | b;
        3'b100: result = a ^ b;
        3'b101: result = a << b;
        3'b110: result = a >> b;
        3'b111: result = $signed(a) >>> b; // XXX check
    endcase

    /* set conditions */
    cc[3] = result[WIDTH-1];
    cc[2] = result == 16'b0;
    cc[1] = (a[WIDTH-1] & b[WIDTH-1]) || // both operands are negative or
        ((a[WIDTH-1] ^ b[WIDTH-1]) && !result[WIDTH-1]); // one of the operands is negative, and the result is positive
    cc[0] = !(a[WIDTH-1] ^ b[WIDTH-1]) && (a[WIDTH-1] ^ result[WIDTH-1]);
end

endmodule
