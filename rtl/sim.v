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

module sim(
    input clk,
    input rst
);

wire [15:0] iaddr;
wire [15:0] idata;

wire [15:0] waddr;
wire [15:0] wdata;
wire we;

wire [15:0] raddr;
wire [15:0] rdata;
wire re;

cpu cpu0(
    .clk(clk),
    .rst(rst),

    .iaddr(iaddr),
    .idata(idata),

    .waddr(waddr),
    .wdata(wdata),
    .we(we),

    .raddr(raddr),
    .rdata(rdata),
    .re(re)
);

dpi_memory imem(
    .clk(clk),
    .rst(rst),

    .raddr(iaddr),
    .rdata(idata),
    .re(1),

    .waddr(0),
    .wdata(0),
    .we(0)
);

dpi_memory #(.INSTANCE(1))
dmem (
    .clk(clk),
    .rst(rst),

    .raddr(raddr),
    .rdata(rdata),
    .re(re),

    .waddr(waddr),
    .wdata(wdata),
    .we(we)
);

endmodule

