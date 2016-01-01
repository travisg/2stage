/*
 * Copyright (c) 2011-2014 Travis Geiselbrecht
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

module testbench(
    input clk
);

int count = 0;
reg rst = 1;
reg halt = 0;

always_ff @(posedge clk) begin
    count <= count + 1;

    if (count == 3) rst <= 0;

    halt <= ((count % 5) == 0) ? 1 : 0;

    if (count == 500) $finish;
end

wire [15:0] addr;
wire [15:0] wdata;
wire [15:0] rdata;
wire re;
wire we;

cpu cpu0(
    .clk(clk),
    .rst(rst),
    .halt(halt),

    .addr(addr),
    .rdata(rdata),
    .wdata(wdata),
    .re(re),
    .we(we)
);

memory mem(
    .clk(clk),
    .rst(rst),

    .raddr(addr),
    .rdata(rdata),
    .re(re),

    .waddr(addr),
    .wdata(wdata),
    .we(we)
);

/*
memory imem(
    .clk(clk),
    .rst(rst),

    .raddr(iaddr),
    .rdata(idata),
    .re(ifetch),

    .waddr(0),
    .wdata(0),
    .we(0)
);

memory dmem(
    .clk(clk),
    .rst(rst),

    .raddr(raddr),
    .rdata(rdata),
    .re(re),
    .rready(rdata_ready),

    .waddr(waddr),
    .wdata(wdata),
    .we(we),
    .wack(wdata_ack)
);
*/

always_comb begin
    $display("count %d, rst %d, addr %h, rdata %h, wdata %h, re %h, we %h", count, rst, addr, rdata, wdata, re, we);
end

initial begin
    //$readmemh("../test.hex", imem.mem);
    $readmemh("../test.hex", mem.mem);
end

endmodule

