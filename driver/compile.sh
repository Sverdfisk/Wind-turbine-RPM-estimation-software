#!/bin/bash
make modules
sudo mkdir -p /lib/modules/$(uname -r)/extra
sudo cp imx385.ko /lib/modules/$(uname -r)/extra/
sudo depmod -a

dtc -I dts -O dtb -@ -o imx385-overlay.dtbo imx385-overlay.dts
sudo cp imx385-overlay.dtbo /boot/firmware/overlays/

