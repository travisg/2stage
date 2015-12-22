all:
	$(MAKE) -C src
	$(MAKE) -C rtl

clean:
	$(MAKE) -C src clean
	$(MAKE) -C rtl clean

.PHONY: all clean
