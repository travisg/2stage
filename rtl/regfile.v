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

module regfile(
    input clk,
    input rst,

    /* port a */
    input [RADDRWIDTH-1:0] raddr_a,
    output [REGWIDTH-1:0] rdata_a,

    /* port b */
    input [RADDRWIDTH-1:0] raddr_b,
    output [REGWIDTH-1:0] rdata_b,

    /* write port */
    input we,
    input [RADDRWIDTH-1:0] waddr,
    input [REGWIDTH-1:0] wdata
);

parameter RADDRWIDTH = 3;
parameter REGWIDTH = 16;

reg [REGWIDTH-1:0] r[2**RADDRWIDTH-1:1];

always_comb begin
    if (raddr_a != 0)
        rdata_a = r[raddr_a];
    else
        rdata_a = 0;

    if (raddr_b != 0)
        rdata_b = r[raddr_b];
    else
        rdata_b = 0;

    $display("regread: [%d] = %x, [%d] = %x", raddr_a, rdata_a, raddr_b, rdata_b);
end

always_ff @(posedge clk) begin
    if (rst) begin
        for (int i = 1; i < 2**RADDRWIDTH; i++)
            r[i] = 0;
    end else begin
        if (we && waddr != 0) begin
            r[waddr] <= wdata;
            $display("regwrite: [%d] = %x", waddr, wdata);
        end
    end
end

endmodule

