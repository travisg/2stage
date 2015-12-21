
SRC := \
	$(wildcard *.asm)

OUT := \
	$(patsubst %.asm,%.hex,$(SRC)) \
	$(patsubst %.asm,%.bin,$(SRC))

#$(warning OUT = $(OUT))

all: $(OUT)

clean:
	rm -f -- $(OUT)

%.hex: %.asm
	../asm/asm.py -x $@ $<

%.bin: %.asm
	../asm/asm.py -o $@ $<

.PHONY: all clean

