BUILD := build
TESTBENCH := $(BUILD)/Vtestbench
SIMULATOR := $(BUILD)/Vsim

SRC := \
	cpu.v \
	memory.v \
	regfile.v

TEST_SRC = testbench.v
SIM_SRC = sim.v dpi_memory.v

EXTRADEPS := test.hex

all: $(TESTBENCH) $(SIMULATOR)

$(TESTBENCH): $(TEST_SRC) $(SRC) testbench.cpp
	mkdir -p $(dir $@)
	verilator -Wno-fatal --top-module testbench --Mdir $(dir $@) -Icpu --exe testbench.cpp --cc -CFLAGS "-DTRACE=1" --trace $(TEST_SRC) $(SRC)
	make -C $(dir $@) -f Vtestbench.mk

$(SIMULATOR): $(SIM_SRC) $(SRC) sim.cpp
	mkdir -p $(dir $@)
	verilator -Wno-fatal --top-module sim --Mdir $(dir $@) -Icpu --exe sim.cpp --cc -CFLAGS "-DSIMULATION -DTRACE=0" --trace $(SIM_SRC) $(SRC)
	make -C $(dir $@) -f Vsim.mk

test.hex:
	make -C ../src
	ln -sf ../src/test.hex

.PHONY: vcd wave sim test.hex

sim: $(SIMULATOR) test.hex
	./$(SIMULATOR) -i test.hex -c 500 -t -o test.bin

vcd: $(TESTBENCH)
	cd $(BUILD); \
	./Vtestbench

wave: vcd
	gtkwave $(BUILD)/trace.vcd

clean::
	rm -f $(EXTRADEPS)
	rm -rf $(BUILD) $(EXTRADEPS)
