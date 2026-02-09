import gc
import vfs
from flashbdev import bdev
from time import sleep_ms
from sys import exit
from micropython import kbd_intr
from machine import RTC

__break_wait_time_seconds = 3

try:
    if bdev:
        vfs.mount(bdev, "/")
except OSError:
    import inisetup

    inisetup.setup()
    
    # Make REPL password bypass file
    f = open("xcore.auth", "w+")
    f.close()

    # Delete allocated objects
    del inisetup, f

gc.collect()

# Start-up pause for recovering break (CTRL-C). It may be by-passed for production
if bool('b R e A k B y P a S s' not in RTC().memory().decode()) == True:

    # Enable CTRL-C
    kbd_intr(3)
    
    try:
        while __break_wait_time_seconds > 0:
            print("Hit CTRL-C to break execution (" + str(__break_wait_time_seconds) + " sec. left)...")
            sleep_ms(1000)
            __break_wait_time_seconds = __break_wait_time_seconds - 1
    except KeyboardInterrupt:

        # Delete all allocated objects
        del __break_wait_time_seconds, sleep_ms, kbd_intr, RTC    
        exit()

    # Restore CTRL-C (disabled)
    kbd_intr(-1)
    
# Delete allocated objects
del __break_wait_time_seconds, sleep_ms, exit, kbd_intr, RTC    
