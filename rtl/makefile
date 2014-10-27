BUILD := build
TESTBENCH := $(BUILD)/testbench
SIMULATOR := $(BUILD)/sim

SRC := \
	cpu.v \
	memory.v \
	regfile.v

TEST_SRC = testbench.v
SIM_SRC = sim.v

#EXTRADEPS := ram.txt makerambanks.py
EXTRADEPS := test2.asm.hex

all: $(TESTBENCH) $(SIMULATOR)

$(TESTBENCH): $(TEST_SRC) $(SRC) testbench.cpp
	mkdir -p $(dir $@)
	verilator -Wno-fatal --top-module testbench --Mdir $(dir $@) -Icpu --exe testbench.cpp --cc -CFLAGS "-DTRACE=1" --trace $(TEST_SRC) $(SRC)
	make -C $(dir $@) -f Vtestbench.mk

$(SIMULATOR): $(SIM_SRC) $(SRC) sim.cpp
	mkdir -p $(dir $@)
	verilator -Wno-fatal --top-module sim --Mdir $(dir $@) -Icpu --exe sim.cpp --cc -CFLAGS "-DSIMULATION -DTRACE=0" --trace $(SIM_SRC) $(SRC)
	make -C $(dir $@) -f Vsim.mk

.PHONY: vcd wave

vcd: $(TESTBENCH)
	cd $(BUILD); \
	./Vtestbench

wave: vcd
	gtkwave $(BUILD)/trace.vcd

clean::
	rm -rf $(BUILD)
