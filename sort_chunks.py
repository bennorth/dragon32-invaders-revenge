import sys

chunks = []
open_chunk = []
for line in sys.stdin:
    if not line.strip():
        chunks.append(open_chunk)
        open_chunk = []
    else:
        open_chunk.append(line)

chunks.append(open_chunk)

def line_sort_key(line):
    pieces = line.split()
    if len(pieces) < 2:
        return line
    else:
        addr = pieces[1]
        return addr

for i_ch, ch in enumerate(chunks):
    if i_ch:
        print()
    for ln in sorted(ch, key=line_sort_key):
        print(ln, end="")
