from os import stat
from machine import reset, mem32
from micropython import kbd_intr
from time import sleep_ms, time
from sys import stdin, stdout
from hashlib import sha256
from binascii import hexlify
from select import poll, POLLIN, select

__PASSWORD_MAX_ATTEMPTS = 3
__AUTHORIZATION_BYPASS_FILENAME = 'xcore.auth'

def __read_esp32_s3_efuse(block_num):
    efuse_map = {
        0: (0x60007000, 17),
        1: (0x60007044, 6),
        2: (0x6000705C, 8),
        3: (0x6000707C, 8),
        4: (0x6000709C, 8),
        5: (0x600070BC, 8),
        6: (0x600070DC, 8),
        7: (0x600070FC, 8),
        8: (0x6000711C, 8),
        9: (0x6000713C, 8),
        10:(0x6000715C, 8)
    }
    
    if block_num not in efuse_map: return
        
    addr, regs = efuse_map[block_num]
    results = []
    for i in range(regs):
        val = mem32[addr + (i * 4)]
        results.append(val)
        
    # Converts to bytes (little-endian)
    blk_bytes = b''.join(int.to_bytes(w, 4, 'little') for w in results)
    return blk_bytes.hex()

def __hash_sha256(password):
    digest = sha256(password.encode('utf-8'))
    return hexlify(digest.digest()).decode('utf-8')

def __hidden_read(prompt="Password: "):
    # Flush stdin
    flush = poll()
    flush.register(stdin, POLLIN)
    while flush.poll(0): stdin.read(1)
    
    # Read from stdin
    stdout.write(prompt)
    password = ""
    while True:
        char = stdin.read(1)
        if char == '\r' or char == '\n': break # Enter
        elif char == '\x7f' or char == '\x08':  # Backspace
            if len(password) > 0: password = password[:-1]
        elif ord(char) >= 32 and ord(char) <= 126:  # Any ASCII char
            password += char
    return password

def __wait_for_enter():
    while True:
        print("Hit ENTER to open console")
        
        # Wait 1 second while checking if input is available
        start = time()
        while time() - start < 1:
            # Check if input is available (non-blocking)
            if select([stdin], [], [], 0)[0]:
                user_input = stdin.read(1)
                if user_input == '\n' or user_input == '\r': return
            sleep_ms(100)

if __name__ == "__main__":
    # Disable CTRL-C
    kbd_intr(-1)    
    
    try:
        stat(__AUTHORIZATION_BYPASS_FILENAME)
        # File 'auth" found in the filesystem: access granted
        
        # Enable CTRL-C
        kbd_intr(3)

        # Delete allocated objects
        del stat, reset, mem32, kbd_intr, sleep_ms, time, stdin, stdout, sha256, hexlify, poll, POLLIN, select
        del __PASSWORD_MAX_ATTEMPTS, __AUTHORIZATION_BYPASS_FILENAME
        del __read_esp32_s3_efuse, __hash_sha256, __hidden_read, __wait_for_enter
    except OSError:
        # File 'auth" not found in the filesystem
       
        # Read REPL password hash from e-fuse BLOCK3
        pwd_block3_hash = __read_esp32_s3_efuse(3)
        if pwd_block3_hash == "0000000000000000000000000000000000000000000000000000000000000000":
            # Password hash not set and still at its default value: access granted

            # Enable CTRL-C
            kbd_intr(3)
            
            # Delete allocated objects
            del stat, reset, mem32, kbd_intr, sleep_ms, time, stdin, stdout, sha256, hexlify, poll, POLLIN, select
            del __PASSWORD_MAX_ATTEMPTS, __AUTHORIZATION_BYPASS_FILENAME
            del __read_esp32_s3_efuse, __hash_sha256, __hidden_read, __wait_for_enter
            del pwd_block3_hash
        else:
            # Password hash set: verification of the provided input password
            
            # Press ENTER to continue
            __wait_for_enter()

            attempts = 0
            while attempts < __PASSWORD_MAX_ATTEMPTS:
                try:
                    pwd = __hidden_read("Password: ").strip()
                    if pwd_block3_hash == __hash_sha256(pwd):
                        # Authorized
                        
                        # Enable CTRL-C
                        kbd_intr(3)
                        
                        # Delete allocated objects
                        del stat, reset, mem32, kbd_intr, sleep_ms, time, stdin, stdout, sha256, hexlify, poll, POLLIN, select
                        del __PASSWORD_MAX_ATTEMPTS, __AUTHORIZATION_BYPASS_FILENAME
                        del __read_esp32_s3_efuse, __hash_sha256, __hidden_read, __wait_for_enter
                        del pwd_block3_hash, attempts, pwd
                        
                        break   
                    else:
                        # Rejected
                        
                        attempts += 1
                        remaining = __PASSWORD_MAX_ATTEMPTS - attempts
                        if remaining <= 0: raise Exception("too many attempts")

                except KeyboardInterrupt:
                    pass
                
                except Exception as e:
                    print("Error:", e)
                    print("Waiting for 10 seconds to reset...")            
                    sleep_ms(10000)
                    reset()
