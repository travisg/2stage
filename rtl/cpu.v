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

    output [IADDRWIDTH-1:0] addr,
    input  [DWIDTH-1:0] rdata,
    output [DWIDTH-1:0] wdata,
    output re,
    output we
);

localparam IADDRWIDTH = 16;
localparam IWIDTH = 16;
localparam DADDRWIDTH = 16;
localparam DWIDTH = 16;

/* shared address bus */
logic ifetch_active;
logic load_active;
logic store_active;
logic [IADDRWIDTH-1:0] ifetch_address;
logic [IADDRWIDTH-1:0] load_store_address;
assign addr = (load_active || store_active) ? load_store_address :
                ifetch_active ? ifetch_address : 16'X;
logic ifetch_bus_cycle = ifetch_active && !(load_active || store_active);

assign re = ifetch_active || load_active;
assign we = store_active;

/* first stage (instruction fetch) */
reg [IADDRWIDTH-1:0] pc;
logic [IADDRWIDTH-1:0] s1_ifetch;
logic [IADDRWIDTH-1:0] pc_next;
logic s1_ifetch_valid;
logic s2_to_s1_take_branch;
logic s2_to_s1_stall;
logic [IADDRWIDTH-1:0] s2_pc_next;

assign ifetch_address = pc_next;

always_comb begin
    if (rst) begin
        pc_next = 16'hffff;
        ifetch_active = 0;
    end else if (s2_to_s1_stall) begin
        pc_next = pc;
        ifetch_active = 1;
    end else begin
        pc_next = s2_to_s1_take_branch ? s2_pc_next : pc + 16'd1; /* default to next instruction */
        ifetch_active = 1;
    end
    s1_ifetch = rdata; /* default to whatever is coming back on the instruction bus */
end

always_ff @(posedge clk) begin
    pc <= pc_next;
    /* should there be valid data in s1_ifetch? */
    s1_ifetch_valid <= ifetch_bus_cycle;
end

always begin
    //$display("S1: pc %x, pc_next %x, ir %x", pc, pc_next, ir);
end

/* second stage */
reg [IADDRWIDTH-1:0] ir = 0;
reg [15:0] mem_immediate;

logic [15:0] mem_immediate_next;

/* special registers */
reg [15:0] reg_lr;
reg [15:0] reg_sp;
reg [3:0]  reg_cc;

logic [15:0] reg_lr_next;
logic [15:0] reg_sp_next;
logic [3:0]  reg_cc_next;

wire reg_cc_n = reg_cc[3];
wire reg_cc_z = reg_cc[2];
wire reg_cc_c = reg_cc[1];
wire reg_cc_v = reg_cc[0];

/* decoder */
wire [4:0] op = ir[15:11];
wire [3:0] alu_op = ir[14:11];
wire [2:0] reg_d = ir[10:8];
wire [2:0] reg_a = ir[7:5];
wire [1:0] reg_b_addr_mode = ir[4:3];
wire [2:0] reg_b = ir[2:0];
wire [15:0] reg_b_imm = ir[3] ? { 12'b111111111111, ir[3:0] } : { 12'b0, ir[3:0] };
wire is_load = (op == 5'b01100);
wire is_store = (op == 5'b01101);

    /* short branches */
wire [3:0] branch_cc = ir[13:10];
wire [15:0] branch_short_offset = ir[9] ? { 6'b111111, ir[9:0] } : { 6'b0, ir[9:0] };
    /* long or register branches */
wire branch_link = ir[9];
wire branch_reg_special = ir[3];
wire [2:0] branch_reg = reg_b;

logic [15:0] reg_a_out;
logic [15:0] reg_b_out;
logic [15:0] reg_d_out;
logic [15:0] alu_a_in;
logic [15:0] alu_b_in;
logic [15:0] alu_result;
logic [3:0] alu_cc;
logic do_reg_writeback;
logic [15:0] writeback_result;
logic reg_d_special;

typedef enum logic [2:0] {
    DECODE,
    IR_IMMEDIATE,
    LS1,
    LS2,
    BRANCH_DELAY
} state_t;
state_t state = DECODE;
state_t state_next;

always_comb begin
    state_next = state;
    mem_immediate_next = mem_immediate;
    reg_cc_next = reg_cc;
    reg_lr_next = reg_lr;
    reg_sp_next = reg_sp;

    reg_d_special = 1'bX;

    s2_pc_next = 16'bX;
    alu_a_in = 16'bX;
    alu_b_in = 16'bX;

    s2_to_s1_take_branch = 0;
    s2_to_s1_stall = 0;

    do_reg_writeback = 0;
    writeback_result = 16'bX;

    load_active = 0;
    store_active = 0;
    wdata = 16'bX;
    load_store_address = 16'bX;

    casez (op)
    5'b10???: begin // branches
        if (branch_cc != 4'b1111) begin
            // short conditional branch
            case (state)
                DECODE: begin
                    // compute target
                    s2_pc_next = pc + branch_short_offset;

                    // check conditions
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
                        /* al */ 4'b1110: s2_to_s1_take_branch = 1;
                        /* nv */ 4'b1111: s2_to_s1_take_branch = 0;
                    endcase

                    // wait one cycle, consuming the instruction the fetcher has already grabbed
                    if (s2_to_s1_take_branch) begin
                        state_next = BRANCH_DELAY;
                    end
                end
                BRANCH_DELAY: begin
                    state_next = DECODE;
                end
                default: ;
            endcase
        end else if (branch_reg_special | branch_reg != 0) begin
            // cc is 1111 and target reg is !0 or bit 3 is set (special register), register branch
            case (state)
                DECODE: begin
                    if (branch_reg_special) begin
                        case (branch_reg)
                            3'd0: s2_pc_next = reg_lr;
                            3'd1: s2_pc_next = reg_sp;
                            default: s2_pc_next = pc; // XXX should be undefined
                        endcase
                    end else begin
                        // plain register target
                        s2_pc_next = reg_b_out;
                    end

                    // take the branch always
                    s2_to_s1_take_branch = 1;

                    // wait one cycle, consuming the instruction the fetcher has already grabbed
                    state_next = BRANCH_DELAY;

                    // handle bl
                    if (branch_link) begin
                       reg_lr_next = pc;
                    end
                end
                BRANCH_DELAY: begin
                    state_next = DECODE;
                end
                default: ;
            endcase
        end else begin
            // cc is 1111 and target reg is 0, load the 16bit immediate in the next instruction word
            case (state)
                DECODE: begin
                    // wait one cycle for the next word of data from stage1 instruction fetcher
                    state_next = IR_IMMEDIATE;
                    mem_immediate_next = s1_ifetch;
                end
                IR_IMMEDIATE: begin
                    // add the 16 bit immediate to pc
                    s2_pc_next = pc + mem_immediate;

                    // take the branch always
                    s2_to_s1_take_branch = 1;

                    // wait one cycle, consuming the instruction the fetcher has already grabbed
                    state_next = BRANCH_DELAY;

                    // handle bl
                    if (branch_link) begin
                       reg_lr_next = pc;
                    end
                end
                BRANCH_DELAY: begin
                    state_next = DECODE;
                end
                default: ;
            endcase
        end
    end // branch op
    5'b00???,
    5'b010??: begin // alu op
        alu_a_in = reg_a_out;
        writeback_result = alu_result;

        // handle the 2nd operand
        casez (reg_b_addr_mode)
            2'b0?: begin // 4 bit signed immediate
                alu_b_in = reg_b_imm;
                do_reg_writeback = 1;
                reg_cc_next = alu_cc;
            end
            2'b10: begin // register b
                // normal case where Rb is treated as a register
                alu_b_in = reg_b_out;
                do_reg_writeback = 1;
                reg_cc_next = alu_cc;
            end
            2'b11: begin // special b address
                if (ir[2]) begin
                    // The instruction wants us to load the next word in the
                    // instruction stream as an immediate.
                    case (state)
                        DECODE: begin
                            // wait one cycle for the next word of data from stage1 instruction fetcher
                            state_next = IR_IMMEDIATE;
                            mem_immediate_next = s1_ifetch;
                        end
                        IR_IMMEDIATE: begin
                            // we've already waited a cycle, so go back to regular DECODE
                            state_next = DECODE;
                            alu_b_in = mem_immediate;
                        end
                        default: ;
                    endcase
                end else begin
                    alu_b_in = 16'd0;
                end

                // if we're at the last cycle of the instruction, decode the rest
                if (state_next == DECODE) begin
                    do_reg_writeback = 1;
                    reg_cc_next = alu_cc;
                    if (ir[1]) begin
                        // special d register
                        do_reg_writeback = 0;
                        case (reg_d)
                            3'd0: reg_lr_next = alu_result;
                            3'd1: reg_sp_next = alu_result;
                            default: ; // XXX should be undefined
                        endcase
                    end
                    if (ir[0]) begin
                        // special a register
                        case (reg_a)
                            3'd0: alu_a_in = reg_lr;
                            3'd1: alu_a_in = reg_sp;
                            default: alu_a_in = 16'd0; // XXX should be undefined
                        endcase
                    end
                end
            end
        endcase
    end // alu op

    5'b0110?: begin // load/store op
        alu_a_in = reg_a_out;
        reg_d_special = 0;

        // handle decoding the 2nd input operand
        casez (reg_b_addr_mode)
            2'b0?: begin // 4 bit signed immediate
                alu_b_in = reg_b_imm;
            end
            2'b10: begin // register b
                // normal case where Rb is treated as a register
                alu_b_in = reg_b_out;
            end
            2'b11: begin // special b address
                if (ir[2]) begin
                    // The instruction wants us to load the next word in the
                    // instruction stream as an immediate.
                    case (state)
                        DECODE: begin
                            // wait one cycle for the next word of data from stage1 instruction fetcher
                            state_next = IR_IMMEDIATE;
                            mem_immediate_next = s1_ifetch;
                        end
                        IR_IMMEDIATE: begin
                            // we've already waited a cycle, so go back to regular DECODE
                            state_next = DECODE;
                            alu_b_in = mem_immediate;
                        end
                        default: ;
                    endcase
                end else begin
                    alu_b_in = 16'd0;
                end

                // decode the d / a regs
                if (ir[1]) begin
                    // special d register
                    reg_d_special = 1;
                end

                if (ir[0]) begin
                    // special a register
                    case (reg_a)
                        3'd0: alu_a_in = reg_lr;
                        3'd1: alu_a_in = reg_sp;
                        default: alu_a_in = 16'd0; // XXX should be undefined
                    endcase
                end
            end
        endcase

        // do the load/store state machine
        if (is_load) begin
            // load, start a 2 stage read operation
            if (state_next != IR_IMMEDIATE) begin
                case (state)
                    IR_IMMEDIATE, DECODE: begin
                        // put the address and data out on the bus, enter LS1 state
                        state_next = LS1;

                        load_store_address = alu_result;
                        load_active = 1;
                        s2_to_s1_stall = 1;
                    end
                    LS1: begin
                        // do the register writeback, wait one more cycle for the instruction fetcher to catch up
                        state_next = LS2;
                        s2_to_s1_stall = 1;

                        if (reg_d_special) begin
                            case (reg_d)
                                3'd0: reg_lr_next = rdata;
                                3'd1: reg_sp_next = rdata;
                                3'd2: ; // XXX implement pc load here
                                3'd3: reg_cc_next = rdata[3:0];
                                default: ; // XXX should be undefined
                            endcase
                        end else begin
                            writeback_result = rdata;
                            do_reg_writeback = 1;
                        end
                    end
                    LS2: begin
                        // if rdata is ready, we can move on to the next instruction
                        state_next = DECODE;
                    end
                    default: ;
                endcase
            end
        end else begin
            // store, dump the result on the bus
            if (state_next != IR_IMMEDIATE) begin
                case (state)
                    IR_IMMEDIATE, DECODE: begin
                        // put the address and data out on the bus
                        state_next = LS1;
                        load_store_address = alu_result;
                        store_active = 1;
                        s2_to_s1_stall = 1;
                        if (reg_d_special) begin
                            case (reg_d)
                                3'd0: wdata = reg_lr;
                                3'd1: wdata = reg_sp;
                                3'd2: wdata = pc;
                                3'd3: wdata = { 12'd0, reg_cc };
                                default: ; // XXX should be undefined
                            endcase
                        end else begin
                            wdata = reg_d_out;
                        end
                    end
                    LS1: begin
                        state_next = LS2;
                        s2_to_s1_stall = 1;
                    end
                    LS2: begin
                        state_next = DECODE;
                    end
                    default: ;
                endcase
            end

            // based on us being in LS1 the next cycle, put the read address out on the bus
            if (state_next == LS1) begin
            end
        end
    end
    5'b0111?: begin // push/pop op
    end
    5'b11???: begin // undefined
    end
    endcase
end

always_ff @(posedge clk) begin
    if (rst) begin
        ir <= 0;
        state <= DECODE;
        mem_immediate <= 0;
        reg_cc <= 0;
        reg_lr <= 0;
        reg_sp <= 0;
    end else begin
        // fetch the next instruction from stage 1
        if (state_next == DECODE) begin
            if (s1_ifetch_valid) begin
                ir <= s1_ifetch;
            end else begin
                ir <= 0; // nop
            end
        end
        state <= state_next;
        mem_immediate <= mem_immediate_next;
        reg_cc <= reg_cc_next;
        reg_lr <= reg_lr_next;
        reg_sp <= reg_sp_next;
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

    .we(do_reg_writeback),
    .waddr(reg_d),
    .wdata(writeback_result)
);

/* alu */
alu alu(
    .op(alu_op),
    .a(alu_a_in),
    .b(alu_b_in),
    .result(alu_result),
    .cc_in(reg_cc),
    .cc_out(alu_cc)
);

endmodule
