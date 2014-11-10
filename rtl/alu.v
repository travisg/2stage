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
    input [3:0] op,

    input [WIDTH-1:0] a,
    input [WIDTH-1:0] b,
    output reg [WIDTH-1:0] result,

    input [3:0] cc_in,
    output logic [3:0] cc_out
);

parameter WIDTH = 16;

wire a_neg = a[WIDTH-1];
wire b_neg = b[WIDTH-1];
wire result_neg = result[WIDTH-1];

wire [WIDTH-1:0] carry_in = { 15'b0, cc_in[1] };

typedef enum logic [1:0] {
    CC_WB_NONE,
    CC_WB_NZCV,
    CC_WB_NZ
} cc_wb_type;
cc_wb_type cc_wb;

always_comb begin
    cc_out = cc_in;
    cc_wb = CC_WB_NONE;

    /* do the op */
    case (op)
        /* mov */ 4'b0000: begin
            result = a + b;
        end
        /* add */ 4'b0001: begin
            cc_wb = CC_WB_NZCV;
            result = a + b + carry_in;
        end
        /* adc */ 4'b0010: begin
            cc_wb = CC_WB_NZCV;
            result = a + b + carry_in;
        end
        /* sub */ 4'b0011: begin
            cc_wb = CC_WB_NZCV;
            result = a - b;
        end
        /* sbc */ 4'b0100: begin
            cc_wb = CC_WB_NZCV;
            result = a - b - carry_in;
        end
        /* and */ 4'b0101: begin
            cc_wb = CC_WB_NZ;
            result = a & b;
        end
        /* or  */ 4'b0110: begin
            cc_wb = CC_WB_NZ;
            result = a | b;
        end
        /* xor */ 4'b0111: begin
            cc_wb = CC_WB_NZ;
            result = a ^ b;
        end
        /* lsl */ 4'b1000: begin
            cc_wb = CC_WB_NZ;
            result = a << b;
        end
        /* lsr */ 4'b1001: begin
            cc_wb = CC_WB_NZ;
            result = a >> b;
        end
        /* asr */ 4'b1010: begin
            cc_wb = CC_WB_NZ;
            result = $signed(a) >>> b; // XXX check
        end
        /* ror */ 4'b1011: begin
            cc_wb = CC_WB_NZ;
            result = ($signed(a) >>> b) | (a << (WIDTH-b)); // XXX check
        end

        /* ldr */ 4'b1100: result = a + b;
        /* str */ 4'b1101: result = a + b;

                  default: result = 16'bX;
    endcase

    /* set conditions depending on op class */
    if (cc_wb == CC_WB_NZ || cc_wb == CC_WB_NZCV) begin
        cc_out[3] = result_neg;
        cc_out[2] = result == 16'b0;
    end
    if (cc_wb == CC_WB_NZCV) begin
        cc_out[1] = (a_neg & b_neg) || // both operands are negative or
            ((a_neg ^ b_neg) && !result_neg); // one of the operands is negative, and the result is positive
        cc_out[0] = !(a_neg ^ b_neg) && (a_neg ^ result_neg);
    end
end

endmodule
