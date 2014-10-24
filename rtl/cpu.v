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
    input  [IWIDTH-1:0] idata,

    output [DADDRWIDTH-1:0] waddr,
    output [DWIDTH-1:0] wdata,
    output we,

    output [DADDRWIDTH-1:0] raddr,
    input  [DWIDTH-1:0] rdata,
    output re
);

localparam IADDRWIDTH = 16;
localparam IWIDTH = 16;
localparam DADDRWIDTH = 16;
localparam DWIDTH = 16;

/* first stage (instruction fetch) */
reg [IADDRWIDTH-1:0] pc;
logic [IADDRWIDTH-1:0] pc_next;
logic [IADDRWIDTH-1:0] s1_ifetch;
logic s2_to_s1_take_branch;
logic s2_to_s1_stall;
logic [15:0] s2_pc_next;

assign iaddr = pc_next;

always_comb begin
    if (s2_to_s1_stall) begin
        pc_next = pc;
    end else begin
        pc_next = s2_to_s1_take_branch ? s2_pc_next : pc + 1; /* default to next instruction */
    end
    s1_ifetch = idata; /* default to whatever is coming back on the instruction bus */
end

always_ff @(posedge clk) begin
    if (rst) begin
        pc <= 16'd-1; // causes the first instruction to be 0
    end else begin
        pc <= pc_next;
    end
end

always begin
    //$display("S1: pc %x, pc_next %x, ir %x", pc, pc_next, ir);
end

/* second stage */
reg [IADDRWIDTH-1:0] ir = 0;
reg [IADDRWIDTH-1:0] ir_next;
reg [15:0] mem_immediate;
reg [15:0] mem_immediate_next;
reg [3:0]  reg_cc;
reg [3:0]  reg_cc_next;

wire reg_cc_n = reg_cc[3];
wire reg_cc_z = reg_cc[2];
wire reg_cc_c = reg_cc[1];
wire reg_cc_v = reg_cc[0];


/* data memory unit */
logic re;
logic [DADDRWIDTH-1:0] raddr;
logic we;
logic [DADDRWIDTH-1:0] waddr;
logic [DWIDTH-1:0] wdata;

/* decoder */
wire [3:0] op = ir[15:12];
wire [2:0] alu_op = ir[14:12];
wire reg_d_indirect = ir[11];
wire [2:0] reg_d = ir[10:8];
wire [2:0] reg_a = ir[7:5];
wire [1:0] reg_b_addr_mode = ir[4:3];
wire [2:0] reg_b = ir[2:0];

wire [3:0] branch_cc = ir[12:9];
wire [15:0] branch_offset = ir[8] ? { 7'b1111111, ir[8:0] } : { 7'b0, ir[8:0] };

logic [15:0] reg_a_out;
logic [15:0] reg_b_out;
logic [15:0] reg_d_out;
logic [15:0] alu_a_in;
logic [15:0] alu_b_in;
logic [15:0] alu_result;
logic [3:0] alu_cc;
logic reg_writeback;

typedef enum [1:0] {
    DECODE,
    IR_IMMEDIATE,
    LOAD1,
    LOAD2
} state_t;
state_t state = DECODE;
state_t state_next;

always_comb begin
    s2_to_s1_take_branch = 0;
    s2_to_s1_stall = 0;
    reg_writeback = 0;
    state_next = state;
    ir_next = s1_ifetch;
    mem_immediate_next = mem_immediate;
    reg_cc_next = reg_cc;
    s2_pc_next = 16'bX;
    alu_a_in = reg_a_out;
    alu_b_in = 16'bX;

    re = 0;
    raddr = 0;
    we = 0;
    waddr = 0;
    wdata = 0;

    casez (op)
    4'b10??: begin // branch
        s2_pc_next = pc + branch_offset;

        /* check conditions */
        case (branch_cc)
            /* eq */ 4'b0000: s2_to_s1_take_branch = reg_cc_z;
            /* ne */ 4'b0001: s2_to_s1_take_branch = !reg_cc_z;
         /* cs|hs */ 4'b0010: s2_to_s1_take_branch = reg_cc_c;
         /* cc|lo */ 4'b0011: s2_to_s1_take_branch = !reg_cc_c;
            /* mi */ 4'b0100: s2_to_s1_take_branch = reg_cc_n;
            /* pl */ 4'b0101: s2_to_s1_take_branch = !reg_cc_n;
            /* vs */ 4'b0110: s2_to_s1_take_branch = reg_cc_v;
            /* vc */ 4'b0111: s2_to_s1_take_branch = !reg_cc_v;
            /* hi */ 4'b1000: s2_to_s1_take_branch = reg_cc_v && !reg_cc_z;
            /* ls */ 4'b1001: s2_to_s1_take_branch = !reg_cc_v || reg_cc_z;
            /* ge */ 4'b1010: s2_to_s1_take_branch = reg_cc_n == reg_cc_v;
            /* lt */ 4'b1011: s2_to_s1_take_branch = reg_cc_n != reg_cc_v;
            /* gt */ 4'b1100: s2_to_s1_take_branch = !reg_cc_z && (reg_cc_n == reg_cc_v);
            /* le */ 4'b1101: s2_to_s1_take_branch = reg_cc_z || (reg_cc_n != reg_cc_v);
            /* nv */ 4'b1110: s2_to_s1_take_branch = 0;
            /* al */ 4'b1111: s2_to_s1_take_branch = 1;
        endcase

        if (ir[13]) begin // link
            // XXX handle link
        end
        //$display("S2: ir %x, branch rd %d, offset %x, s2_pc_next %x, take branch %d", ir, reg_d, branch_offset, s2_pc_next, s2_to_s1_take_branch);
    end
    4'b11??: begin // undefined
    end
    4'b0???: begin // alu op
        // handle the 2nd operand
        casez (reg_b_addr_mode)
            2'b0?: begin // 4 bit signed immediate
                alu_b_in = ir[3] ? { 12'b111111111111, ir[3:0] } : { 12'b0, ir[3:0] };
                reg_writeback = 1;
                reg_cc_next = alu_cc;
            end
            2'b10: begin // register b
                if (reg_b == 0) begin
                    // special case: Rb == 0. The instruction wants us to load the next word in the
                    // instruction stream as an immediate.
                    case (state)
                        DECODE: begin
                            // wait one cycle for the next word of data from stage1 instruction fetcher
                            state_next = IR_IMMEDIATE;
                            ir_next = ir;
                            mem_immediate_next = s1_ifetch;
                        end
                        IR_IMMEDIATE: begin
                            // we've already waited a cycle, so go back to regular DECODE
                            state_next = DECODE;
                            reg_writeback = 1;
                            reg_cc_next = alu_cc;
                            alu_b_in = mem_immediate;
                        end
                        default: ;
                    endcase
                end else begin
                    // normal case where Rb is treated as a register
                    alu_b_in = reg_b_out;
                    reg_writeback = 1;
                    reg_cc_next = alu_cc;
                end
            end
            2'b11: begin // register b indirect
                if (reg_b == 0) begin
                    // special case, Rb == 0, indirect
                    // return PC
                    alu_b_in = pc;
                    reg_writeback = 1;
                    reg_cc_next = alu_cc;
                end else begin
                    // start a 2 stage read operation
                    case (state)
                        DECODE: begin
                            // put the address and data out on the bus
                            state_next = LOAD1;
                            raddr = reg_b_out;
                            re = 1;
                            ir_next = ir;
                            s2_to_s1_stall = 1;
                        end
                        LOAD1: begin
                            // let it sit for a clock for the external memory to respond
                            mem_immediate_next = rdata;
                            state_next = LOAD2;
                            ir_next = ir;
                            s2_to_s1_stall = 1;
                        end
                        LOAD2: begin
                            // we should have it now, go back to regular decode
                            state_next = DECODE;
                            reg_cc_next = alu_cc;
                            reg_writeback = 1;
                            alu_b_in = mem_immediate;
                        end
                        default: ;
                    endcase
                end
            end
        endcase

        // handle indirect d writebacks
        if (reg_d_indirect && reg_writeback) begin
            if (reg_d != 0) begin
                // once we've handled the read states (if any), start a write cycle
                // note, this can overlap with the last cycle of a read
                reg_writeback = 0;
                we = 1;
                waddr = reg_d_out;
                wdata = alu_result;
            end else begin
                // reg_d == 0 is a special case, writes to the pc (branches)
                reg_writeback = 0;
                s2_pc_next = alu_result;
                s2_to_s1_take_branch = 1;
            end
        end

        //$display("S2: ir %x, wb %d, alu rd %d, ra %d, rb %d", ir, reg_writeback, reg_d, reg_a, reg_b);
    end
    endcase

end

always_ff @(posedge clk) begin
    if (rst) begin
        ir <= 0;
        state <= 0;
        mem_immediate <= 0;
        reg_cc <= 0;
    end else begin
        ir <= ir_next;
        state <= state_next;
        mem_immediate <= mem_immediate_next;
        reg_cc <= reg_cc_next;
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

    .raddr_c(reg_d),
    .rdata_c(reg_d_out),

    .we(reg_writeback),
    .waddr(reg_d),
    .wdata(alu_result)
);

/* alu */
alu alu(
    .op(alu_op),
    .a(alu_a_in),
    .b(alu_b_in),
    .result(alu_result),
    .cc(alu_cc)
);

endmodule
