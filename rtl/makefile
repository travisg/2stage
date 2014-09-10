BUILD := build
TESTBENCH := $(BUILD)/testbench

SRC := \
	cpu.v \
	memory.v \
	regfile.v

#SRC += ../lib/library.v
SRC += testbench.v

#EXTRADEPS := ram.txt makerambanks.py
EXTRADEPS := test2.asm.hex

all: $(TESTBENCH)

$(TESTBENCH): $(SRC) testbench.cpp
	mkdir -p $(dir $@)
	verilator -Wno-fatal --top-module testbench --Mdir $(dir $@) -Icpu --exe testbench.cpp --cc -DSIMULATION -CFLAGS -DTRACE --trace $(SRC)
	make -C $(dir $@) -f Vtestbench.mk

.PHONY: vcd wave

vcd: $(TESTBENCH)
	cd $(BUILD); \
	./Vtestbench

wave: vcd
	gtkwave $(BUILD)/trace.vcd

clean::
	rm -rf $(BUILD)
