import sys

next_id_ = 80
def next_id():
    global next_id_
    next_id_ += 1
    return next_id_

for line in map(str.strip, open("vars.txt", "rt")):
    pieces = line.split(None, 3)
    if len(pieces) == 0 or pieces[0].startswith("#"):
        continue

    kind = pieces[0]
    addr = pieces[1]

    qual = "Var" if kind in "bwsp" else "Const"

    name = f"{qual}_{kind}_" + (str(next_id()) if len(pieces) < 3 else pieces[2])
    comment = None if len(pieces) < 4 else pieces[3]

    print(f"COMMENT {addr} <DCHUNK>")
    if comment is not None:
        print(f"COMMENT {addr} {comment}")
    print(f"LABEL {addr} {name}")

    if kind in "bB":
        next_addr = hex(int(addr, 16) + 1).upper()[2:]
        print(f"HEX {addr}")

    if kind in "wWpPsS":
        next_addr = hex(int(addr, 16) + 2).upper()[2:]
        low_addr = hex(int(addr, 16) + 1).upper()[2:]
        print(f"WORD {addr}")
        if kind not in "pPsS":
            print(f"CONST {addr}-{low_addr}")

    print(f"PREPCOMM {next_addr} </DCHUNK>")
