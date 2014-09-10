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


module cpu(
    input clk,
    input rst,

    output [IADDRWIDTH-1:0] iaddr,
    input  [IWIDTH-1:0] idata

);

localparam IADDRWIDTH = 16;
localparam IWIDTH = 16;

/* first stage (instruction fetch) */
reg [IADDRWIDTH-1:0] pc;
logic [IADDRWIDTH-1:0] pc_next;
reg [IADDRWIDTH-1:0] ir = 0;
logic [IADDRWIDTH-1:0] ir_next;

assign iaddr = pc;

always_comb begin
    pc_next = pc + 1; /* default to next instruction */
    ir_next = idata; /* default to whatever is coming back on the instruction bus */
end

always_ff @(posedge clk) begin
    if (rst) begin
        pc <= 0;
        ir <= 0;
    end else begin
        if (s2_to_s1_take_branch) begin
            pc <= s2_pc_next;
        end else begin
            pc <= pc_next;
        end
        ir <= ir_next;
    end
end

always begin
    $display("S1: pc %x, pc_next %x, ir %x", pc, pc_next, ir);
end

/* second stage */
logic [2:0] reg_d;
logic [2:0] reg_a;
logic [2:0] reg_b;
logic [2:0] alu_op;
logic decode_branch;
logic [15:0] offset;
logic [15:0] s2_pc_next;
logic s2_to_s1_take_branch;

logic [15:0] reg_a_out;
logic [15:0] reg_b_out;

logic [15:0] alu_result;

always_comb begin
    reg_a = ir[14:12];
    reg_d = ir[11:9];
    reg_b = ir[8:6];
    decode_branch = ir[15];
    s2_pc_next = 16'bX;
    s2_to_s1_take_branch = 0;
    alu_op = ir[2:0];
    alu_result = 16'bX;

    // decode branch offset, sign extended to 16 bits
    if (ir[11])
        offset = { 5'b11111, ir[10:0] };
    else
        offset = { 5'b00000, ir[10:0] };

    if (decode_branch) begin
        s2_pc_next = pc + offset;
        s2_to_s1_take_branch = (reg_a_out == 0);
        $display("S2: ir %x, branch rd %d, offset %x, s2_pc_next %x, take branch %d", ir, reg_d, offset, s2_pc_next, s2_to_s1_take_branch);
    end else begin
        case (alu_op)
        3'b000: begin // ADD
            alu_result = reg_a_out + reg_b_out;
        end
///



        endcase
        $display("S2: ir %x, alu rd %d, ra %d, rb %d", ir, reg_d, reg_a, reg_b);
    end
end

/* register file */
regfile regs(
    .clk(clk),
    .rst(rst),

    .raddr_a(reg_a),
    .rdata_a(reg_a_out),

    .raddr_b(reg_b),
    .rdata_b(reg_b_out),

    .we(0),
    .waddr(0),
    .wdata(0)
);

endmodule
