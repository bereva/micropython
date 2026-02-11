import gc
import vfs
from flashbdev import bdev
from time import sleep_ms
from sys import exit
from micropython import kbd_intr
from machine import RTC
from os import stat

__BREAK_WAIT_TIME_SECONDS = 3
__FORCE_BREAK_FILENAME = 'xcore.break'

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
        # Check for break-force file in the filesystem
        try: stat(__FORCE_BREAK_FILENAME)
        except OSError:
            print(__FORCE_BREAK_FILENAME + " file found: breaking execution...")
            raise KeyboardInterrupt
        
        # Start countdown
        while __BREAK_WAIT_TIME_SECONDS > 0:
            print("Hit CTRL-C to break execution (" + str(__BREAK_WAIT_TIME_SECONDS) + " sec. left)...")
            sleep_ms(1000)
            __BREAK_WAIT_TIME_SECONDS = __BREAK_WAIT_TIME_SECONDS - 1
    except KeyboardInterrupt:

        # Delete all allocated objects
        del __BREAK_WAIT_TIME_SECONDS, __FORCE_BREAK_FILENAME, sleep_ms, kbd_intr, RTC, stat
        exit()

    # Restore CTRL-C (disabled)
    kbd_intr(-1)
    
# Delete allocated objects
del __BREAK_WAIT_TIME_SECONDS, __FORCE_BREAK_FILENAME, sleep_ms, exit, kbd_intr, RTC, stat
