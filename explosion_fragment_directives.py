addr = 0x3bfd
while addr < 0x3cc3:
    print(f"WORD {addr:04X}-{(addr+3):04X}")
    print(f"CONST {addr:04X}-{(addr+3):04X}")
    print(f"HEX {(addr+4):04X}-{(addr+5):04X}")
    addr += 6
