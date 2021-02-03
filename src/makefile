
SRC := \
	$(wildcard *.asm)

OUT := \
	$(patsubst %.asm,%.hex,$(SRC)) \
	$(patsubst %.asm,%.hex2,$(SRC)) \
	$(patsubst %.asm,%.bin,$(SRC))

#$(warning OUT = $(OUT))

all: $(OUT)

clean:
	rm -f -- $(OUT)

%.hex: %.asm
	../asm/asm.py -x $@ $<

%.hex2: %.asm
	../asm/asm.py -X $@ $<

%.bin: %.asm
	../asm/asm.py -o $@ $<

.PHONY: all clean

