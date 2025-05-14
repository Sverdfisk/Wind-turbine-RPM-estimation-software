import time
import atexit
import gpiod
from gpiod.line import Direction, Value

def reset_all_pins():
    try:
        chip = gpiod.Chip("/dev/gpiochip0")
        req = chip.request_lines(config, consumer="cleanup")
        
        # Set all pins in the config to INACTIVE
        for pin in config.keys():
            req.set_value(pin, Value.INACTIVE)
        
        # Clean up
        req.release()
        chip.close()
        print("All pins reset to INACTIVE")
    except Exception as e:
        print(f"Error resetting pins: {e}")


LS, CLK, XCLR = 23, 25, 26

# 1. Describe how each line should behave
config = {
    LS:   gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE, active_low=False),
    CLK:  gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE, active_low=False),
    XCLR: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE, active_low=False),
}

# 2. Grab the lines in one atomic request
with gpiod.Chip("/dev/gpiochip0") as chip:
    with chip.request_lines(config, consumer="windturbine") as req:
        
        # 3. Drive them
        req.set_value(LS, Value.ACTIVE)
        time.sleep(0.1)

        req.set_value(CLK, Value.ACTIVE)
        time.sleep(0.1)

        req.set_value(XCLR, Value.ACTIVE)

        #while True:
        time.sleep(1)
atexit.register(reset_all_pins)
