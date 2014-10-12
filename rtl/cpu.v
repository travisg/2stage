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
logic [IADDRWIDTH-1:0] s1_ifetch;

assign iaddr = pc;

always_comb begin
    pc_next = pc + 1; /* default to next instruction */
    s1_ifetch = idata; /* default to whatever is coming back on the instruction bus */
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
    end
end

always begin
    $display("S1: pc %x, pc_next %x, ir %x", pc, pc_next, ir);
end

/* second stage */
reg [IADDRWIDTH-1:0] ir = 0;

/* decoder */
wire [3:0] op = ir[15:12];
wire [2:0] reg_a = ir[11:9];
wire reg_d_indirect = ir[8];;
wire [2:0] reg_d = ir[7:5];
wire [1:0] reg_b_addr_mode = ir[4:3];
wire [2:0] reg_b = ir[2:0];

logic [15:0] branch_offset;
logic [15:0] s2_pc_next;
logic s2_to_s1_take_branch;

logic [15:0] reg_a_out;
logic [15:0] reg_b_out;
logic [15:0] alu_result;
logic reg_writeback;

always_comb begin
    s2_pc_next = 16'bX;
    s2_to_s1_take_branch = 0;
    reg_writeback = 0;
    alu_result = 16'bX;
    branch_offset = ir[8] ? { 7'b1111111, ir[8:0] } : { 7'b0, ir[8:0] };

    casez (op)
    4'b110?: begin // branch
        s2_pc_next = pc + branch_offset;
        s2_to_s1_take_branch = ir[12] ? (reg_a_out != 0) : (reg_a_out == 0);
        $display("S2: ir %x, branch rd %d, offset %x, s2_pc_next %x, take branch %d", ir, reg_d, branch_offset, s2_pc_next, s2_to_s1_take_branch);
    end
    4'b111?: begin // undefined
    end
    default: begin // alu op
        // handle the 2nd operand
        logic [15:0] alu_b_in;
        casez (reg_b_addr_mode)
            2'b0?: begin // 4 bit signed immediate
                alu_b_in = ir[3] ? { 12'b111111111111, ir[3:0] } : { 12'b0, ir[3:0] };
            end
            2'b10: begin
                if (reg_b == 0)
                    alu_b_in = 0; // XXX next instruction fetch handle
                else
                    alu_b_in = reg_b_out;
            end
            2'b11: begin // XXX register b indirect, handle
                alu_b_in = 0;
            end
        endcase

        // do the alu op
        case (op)
            4'b0000: alu_result = reg_a_out + alu_b_in;
            4'b0001: alu_result = reg_a_out - alu_b_in;
            4'b0010: alu_result = reg_a_out & alu_b_in;
            4'b0011: alu_result = reg_a_out | alu_b_in;
            4'b0100: alu_result = reg_a_out ^ alu_b_in;
            4'b0101: alu_result = reg_a_out << alu_b_in;
            4'b0110: alu_result = reg_a_out >> alu_b_in;
            4'b0111: alu_result = reg_a_out >>> alu_b_in; // XXX check
            4'b1000: alu_result = (reg_a_out == alu_b_in) ? 1 : 0;
            4'b1001: alu_result = (reg_a_out < alu_b_in) ? 1 : 0;
            4'b1010: alu_result = (reg_a_out <= alu_b_in) ? 1 : 0;
            default: ;
        endcase
        reg_writeback = 1;
        $display("S2: ir %x, wb %d, alu rd %d, ra %d, rb %d", ir, reg_writeback, reg_d, reg_a, reg_b);
    end
    endcase

    // handle indirect d writebacks
end

always_ff @(posedge clk) begin
    ir <= s1_ifetch;
end

/* register file */
regfile regs(
    .clk(clk),
    .rst(rst),

    .raddr_a(reg_a),
    .rdata_a(reg_a_out),

    .raddr_b(reg_b),
    .rdata_b(reg_b_out),

    .we(reg_writeback),
    .waddr(reg_d),
    .wdata(alu_result)
);

endmodule
