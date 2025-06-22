# https://www.kernel.org/doc/Documentation/kbuild/makefiles.txt
obj-m	+= imx385.o

KERNEL := $(shell uname -r)
LINUX_DIR=/lib/modules/$(KERNEL)/build

modules:
	$(MAKE) -C $(LINUX_DIR) M='$(PWD)' modules
