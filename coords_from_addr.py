import sys

addr = int(sys.argv[1], 16);
row, col = divmod(addr - 0x0600, 32)

fmt = "lbl" if len(sys.argv) > 2 and sys.argv[2] == "lbl" else "paren"

if fmt == "lbl":
    print(f"Loc_x{(col * 4):03d}_y{row:03d}")
else:
    print(f"({col * 4}, {row})")
