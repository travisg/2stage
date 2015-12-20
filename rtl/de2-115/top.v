// --------------------------------------------------------------------
// Copyright (c) 2010 by Terasic Technologies Inc.
// --------------------------------------------------------------------
//
// Permission:
//
//   Terasic grants permission to use and modify this code for use
//   in synthesis for all Terasic Development Boards and Altera Development
//   Kits made by Terasic.  Other use of this code, including the selling
//   ,duplication, or modification of any portion is strictly prohibited.
//
// Disclaimer:
//
//   This VHDL/Verilog or C/C++ source code is intended as a design reference
//   which illustrates how these types of functions can be implemented.
//   It is the user's responsibility to verify their design for
//   consistency and functionality through the use of formal
//   verification methods.  Terasic provides no warranty regarding the use
//   or functionality of this code.
//
// --------------------------------------------------------------------
//
//                     Terasic Technologies Inc
//                     356 Fu-Shin E. Rd Sec. 1. JhuBei City,
//                     HsinChu County, Taiwan
//                     302
//
//                     web: http://www.terasic.com/
//                     email: support@terasic.com
//
// --------------------------------------------------------------------
//
// Major Functions: DE2_115 Top Entity Reference Design
//
// --------------------------------------------------------------------
//
// Revision History :
// --------------------------------------------------------------------
//   Ver  :| Author                    :| Mod. Date :| Changes Made:
//   V1.0 :| Richard                   :| 07/09/10  :| Initial Revision
// --------------------------------------------------------------------
module top(

    //////// CLOCK //////////
    input                       CLOCK_50,
    input                       CLOCK2_50,
    input                       CLOCK3_50,
    input                       ENETCLK_25,

    //////// Sma //////////
    //input                       SMA_CLKIN,
    //output                      SMA_CLKOUT,

    //////// LED //////////
    output           [8:0]      LEDG,
    output           [17:0]     LEDR,

    //////// KEY //////////
    input            [3:0]      KEY,

    //////// SW //////////
    input            [17:0]     SW,

    //////// SEG7 //////////
    output           [6:0]      HEX0,
    output           [6:0]      HEX1,
    output           [6:0]      HEX2,
    output           [6:0]      HEX3,
    output           [6:0]      HEX4,
    output           [6:0]      HEX5,
    output           [6:0]      HEX6,
    output           [6:0]      HEX7,

    //////// LCD //////////
    //output                      LCD_BLON,
    //inout            [7:0]      LCD_DATA,
    //output                      LCD_EN,
    //output                      LCD_ON,
    //output                      LCD_RS,
    //output                      LCD_RW,

    //////////// RS232 //////////
    //output                      UART_CTS,
    //input                       UART_RTS,
    input                       UART_RXD,
    output                      UART_TXD,

    //////////// PS2 //////////
    //inout                       PS2_CLK,
    //inout                       PS2_DAT,
    //inout                       PS2_CLK2,
    //inout                       PS2_DAT2,

    //////////// SDCARD //////////
    //output                      SD_CLK,
    //inout                       SD_CMD,
    //inout            [3:0]      SD_DAT,
    //input                       SD_WP_N,

    //////////// VGA //////////
    //output           [7:0]      VGA_B,
    //output                      VGA_BLANK_N,
    //output                      VGA_CLK,
    //output           [7:0]      VGA_G,
    //output                      VGA_HS,
    //output           [7:0]      VGA_R,
    //output                      VGA_SYNC_N,
    //output                      VGA_VS,

    //////////// Audio //////////
    //input                       AUD_ADCDAT,
    //inout                       AUD_ADCLRCK,
    //inout                       AUD_BCLK,
    //output                      AUD_DACDAT,
    //inout                       AUD_DACLRCK,
    //output                      AUD_XCK,

    //////////// I2C for EEPROM //////////
    //output                      EEP_I2C_SCLK,
    //inout                       EEP_I2C_SDAT,

    //////////// I2C for Audio and Tv-Decode //////////
    //output                      I2C_SCLK,
    //inout                       I2C_SDAT,

    //////////// Ethernet 0 //////////
    //output                      ENET0_GTX_CLK,
    //input                       ENET0_INT_N,
    //output                      ENET0_MDC,
    //inout                       ENET0_MDIO,
    //output                      ENET0_RST_N,
    //input                       ENET0_RX_CLK,
    //input                       ENET0_RX_COL,
    //input                       ENET0_RX_CRS,
    //input            [3:0]      ENET0_RX_DATA,
    //input                       ENET0_RX_DV,
    //input                       ENET0_RX_ER,
    //input                       ENET0_TX_CLK,
    //output           [3:0]      ENET0_TX_DATA,
    //output                      ENET0_TX_EN,
    //output                      ENET0_TX_ER,
    //input                       ENET0_LINK100,

    //////////// Ethernet 1 //////////
    //output                      ENET1_GTX_CLK,
    //input                       ENET1_INT_N,
    //output                      ENET1_MDC,
    //inout                       ENET1_MDIO,
    //output                      ENET1_RST_N,
    //input                       ENET1_RX_CLK,
    //input                       ENET1_RX_COL,
    //input                       ENET1_RX_CRS,
    //input            [3:0]      ENET1_RX_DATA,
    //input                       ENET1_RX_DV,
    //input                       ENET1_RX_ER,
    //input                       ENET1_TX_CLK,
    //output           [3:0]      ENET1_TX_DATA,
    //output                      ENET1_TX_EN,
    //output                      ENET1_TX_ER,
    //input                       ENET1_LINK100,

    //////////// TV Decoder 1 //////////
    //input                       TD_CLK27,
    //input            [7:0]      TD_DATA,
    //input                       TD_HS,
    //output                      TD_RESET_N,
    //input                       TD_VS,


    //////////// USB OTG controller //////////
    //inout            [15:0]     OTG_DATA,
    //output           [1:0]      OTG_ADDR,
    //output                      OTG_CS_N,
    //output                      OTG_WR_N,
    //output                      OTG_RD_N,
    //input            [1:0]      OTG_INT,
    //output                      OTG_RST_N,
    //input            [1:0]      OTG_DREQ,
    //output           [1:0]      OTG_DACK_N,
    //inout                       OTG_FSPEED,
    //inout                       OTG_LSPEED,

    //////////// IR Receiver //////////
    //input                       IRDA_RXD,

    //////////// SDRAM //////////
    //output          [12:0]      DRAM_ADDR,
    //output           [1:0]      DRAM_BA,
    //output                      DRAM_CAS_N,
    //output                      DRAM_CKE,
    //output                      DRAM_CLK,
    //output                      DRAM_CS_N,
    //inout           [31:0]      DRAM_DQ,
    //output           [3:0]      DRAM_DQM,
    //output                      DRAM_RAS_N,
    //output                      DRAM_WE_N,

    //////////// SRAM //////////
    //output          [19:0]      SRAM_ADDR,
    //output                      SRAM_CE_N,
    //inout           [15:0]      SRAM_DQ,
    //output                      SRAM_LB_N,
    //output                      SRAM_OE_N,
    //output                      SRAM_UB_N,
    //output                      SRAM_WE_N,

    //////////// Flash //////////
    //output          [22:0]      FL_ADDR,
    //output                      FL_CE_N,
    //inout            [7:0]      FL_DQ,
    //output                      FL_OE_N,
    //output                      FL_RST_N,
    //input                       FL_RY,
    //output                      FL_WE_N,
    //output                      FL_WP_N,

    //////////// GPIO //////////
    inout           [35:0]      GPIO,

    //////////// HSMC (LVDS) //////////
//    input                       HSMC_CLKIN_N1,
//    input                       HSMC_CLKIN_N2,
//    input                       HSMC_CLKIN_P1,
//    input                       HSMC_CLKIN_P2,
//    input                       HSMC_CLKIN0,
//    output                      HSMC_CLKOUT_N1,
//    output                      HSMC_CLKOUT_N2,
//    output                      HSMC_CLKOUT_P1,
//    output                      HSMC_CLKOUT_P2,
//    output                      HSMC_CLKOUT0,
//    inout           [3:0]       HSMC_D,
//    input           [16:0]      HSMC_RX_D_N,
//    input           [16:0]      HSMC_RX_D_P,
//    output          [16:0]      HSMC_TX_D_N,
//    output          [16:0]      HSMC_TX_D_P,

    //////// EXTEND IO //////////
    inout           [6:0]       EX_IO
);

//assign HEX0 = 7'h7f;
//assign HEX1 = 7'h7f;
//assign HEX2 = 7'h7f;
//assign HEX3 = 7'h7f;
//assign HEX4 = 7'h7f;
//assign HEX5 = 7'h7f;
//assign HEX6 = 7'h7f;
//assign HEX7 = 7'h7f;

//assign LEDG = 9'h0;
//assign LEDR = 18'h0;

wire [15:0] cpu_addr;
wire [15:0] cpu_wdata;
wire [15:0] cpu_rdata;
wire cpu_re;
wire cpu_we;

wire in_clk = CLOCK_50;

logic clk;
logic rst;

reg [24:0] counter = 0;

always_ff @(posedge in_clk) begin
    counter <= counter + 1;
    rst <= ~KEY[0];
end

assign clk = SW[0] ? counter[24] : in_clk;

cpu cpu0(
    .clk(clk),
    .rst(rst),

    .addr(cpu_addr),
    .re(cpu_re),
    .we(cpu_we),
    .wdata(cpu_wdata),
    .rdata(cpu_rdata)
);

wire [15:0] mem_addr;
wire [15:0] mem_wdata;
wire [15:0] mem_rdata;
wire mem_re;
wire mem_we;

memory #(.AWIDTH(8), .MEMH_FILE("../test.hex"))
mem(
    .clk(clk),
    .rst(rst),

    .raddr(mem_addr),
    .rdata(mem_rdata),
    .re(mem_re),

    .waddr(mem_addr),
    .wdata(mem_wdata),
    .we(mem_we)
);

wire io_addr;
wire [31:0] io_wdata;
wire [31:0] io_rdata;
wire io_re;
wire io_we;
wire [3:0] io_byteenable;

ip ip(
    .clk(in_clk),
    .reset(rst),
    .irq(),
    .address(io_addr),
    .chipselect(io_re || io_we),
    .byteenable(io_byteenable),
    .read(io_re),
    .write(io_we),
    .writedata(io_wdata),
    .readdata(io_rdata),
    .UART_RXD(UART_RXD),
    .UART_TXD(UART_TXD)
);

typedef enum logic [0:0] {
    MEM,
    IO
} device_read_sel_t;
device_read_sel_t device_read_sel = MEM;
device_read_sel_t device_read_sel_next;

// bus decoder
always_comb begin
    // defaults for memory
    mem_re = 0;
    mem_we = 0;
    mem_addr = { 8'd0, cpu_addr };
    mem_wdata = cpu_wdata;

    // defaults for io
    io_re = 0;
    io_we = 0;
    io_addr = cpu_addr[1];
    io_wdata = 32'bX;
    io_byteenable = 4'bX;

    if (cpu_addr < 'hf000) begin
        mem_re = cpu_re;
        mem_we = cpu_we;
        device_read_sel_next = MEM;
    end else begin
        io_re = cpu_re;
        io_we = cpu_we;
        io_byteenable = cpu_addr[0] ? 4'b1100 : 4'b0011;
        device_read_sel_next = IO;
        io_wdata = { cpu_wdata, cpu_wdata };
    end

    // the read path back to the cpu lags behind by a clock, which is tracked
    // in the device_read_sel register
    case (device_read_sel)
    MEM: begin
        cpu_rdata = mem_rdata;
    end
    IO: begin
        cpu_rdata = cpu_addr[0] ? io_rdata[31:16] : io_rdata[15:0];
    end
    endcase
end

always_ff @(posedge clk) begin
    device_read_sel <= device_read_sel_next;
end

assign LEDR = { cpu_we, cpu_re, cpu_addr };
assign LEDG = 0;

seven_segment s0(cpu_rdata[3:0], HEX0);
seven_segment s1(cpu_rdata[7:4], HEX1);
seven_segment s2(cpu_rdata[11:8], HEX2);
seven_segment s3(cpu_rdata[15:12], HEX3);

seven_segment s4(cpu_addr[3:0], HEX4);
seven_segment s5(cpu_addr[7:4], HEX5);
seven_segment s6(cpu_addr[11:8], HEX6);
seven_segment s7(cpu_addr[15:12], HEX7);

endmodule

