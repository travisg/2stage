# 2stage
A simple 2 stage cpu in verilog

8 16-bit general purpose registers, 16 bit address/data bus.

## Files/Paths to note
* [isa.txt](isa.txt) - The instruction set
* [rtl](rtl) - Verilog implementation
  * [rtl/de2-115](rtl/de2-115) - Altera Quartus project for DE-115 fpga board
* [asm](asm) - Python based assembler
* [src](src) - Assembly code

## Requirements

[Verilator](http://www.veripool.org/wiki/verilator) required for implementation of test bench and simulator.

FPGA project implemented using Altera Quartus 15.1 Lite.
