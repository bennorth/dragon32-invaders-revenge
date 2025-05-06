import sys

addr = int(sys.argv[1], 16);
row, col = divmod(addr - 0x0600, 32)
print(f"({col * 4}, {row})")
