BUILD := build
TESTBENCH := $(BUILD)/Vtestbench
SIMULATOR := $(BUILD)/Vsim

SRC := \
	cpu.v \
	memory.v \
	regfile.v

TEST_SRC = testbench.v
SIM_SRC = sim.v dpi_memory.v

all: $(TESTBENCH) $(SIMULATOR)

$(TESTBENCH): $(TEST_SRC) $(SRC) testbench.cpp $(BUILD)/test.hex
	mkdir -p $(dir $@)
	verilator -Wno-fatal --top-module testbench --Mdir $(dir $@) -Icpu --exe testbench.cpp --cc -CFLAGS "-DTRACE=1" --trace $(TEST_SRC) $(SRC)
	make -C $(dir $@) -f Vtestbench.mk

$(SIMULATOR): $(SIM_SRC) $(SRC) sim.cpp
	mkdir -p $(dir $@)
	verilator -Wno-fatal --top-module sim --Mdir $(dir $@) -Icpu --exe sim.cpp --cc -CFLAGS "-DSIMULATION -DTRACE=0" --trace $(SIM_SRC) $(SRC)
	make -C $(dir $@) -f Vsim.mk

sim: $(SIMULATOR) $(BUILD)/test.hex
	./$(SIMULATOR) -im $(BUILD)/test.hex

../src/test.hex:
	make -C ../src

$(BUILD)/test.hex: ../src/test.hex
	mkdir -p $(dir $@)
	ln -f $< $@

.PHONY: vcd wave sim

vcd: $(TESTBENCH)
	cd $(BUILD); \
	./Vtestbench

wave: vcd
	gtkwave $(BUILD)/trace.vcd

clean::
	rm -rf $(BUILD) $(EXTRADEPS)
