import sys

sys_mpy = sys.implementation._mpy

print("arch: ", end='')

try:
    arch = [None, 'x86', 'x64', 'armv6', 'armv6m', 'armv7m', 'armv7em', 
        'armv7emsp', 'armv7emdp', 'xtensa', 'xtensawin'][sys_mpy >> 10]
    print(arch)
    
except:
    print('unknown')