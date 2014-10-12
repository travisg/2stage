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

module memory(
    input clk,
    input rst,

    input re,
    input [AWIDTH-1:0] raddr,
    output reg [DWIDTH-1:0] rdata,

    input we,
    input [AWIDTH-1:0] waddr,
    input [DWIDTH-1:0] wdata
);

parameter AWIDTH = 16;
parameter DWIDTH = 16;

reg [AWIDTH-1:0] raddr_reg;

reg [DWIDTH-1:0] mem [2**DWIDTH-1:0];

/* zero out or register the read */
always_ff @(posedge clk) begin
    if (rst) begin
        rdata <= 0;
    end else begin
        if (re) begin
            rdata <= mem[raddr];
        end

        if (we) begin
            mem[waddr] <= wdata;
        end
    end
end



endmodule
