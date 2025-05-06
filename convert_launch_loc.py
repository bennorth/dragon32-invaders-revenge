s_launch_locs = \
    "$0B1F,$12DF,$173F,$0E5F,$109F,$11BF,$0C1F,$14BF,$19BF,$0F7F,$0D3F,$15FF,$187F"

launch_locs = [int(s[1:], 16) for s in s_launch_locs.split(",")]

locs = []
for ptr in launch_locs:
    within_scr = ptr - 0x0600
    row, col = divmod(within_scr, 32)
    locs.append((row, col))

#locs.sort()
print(', '.join(str(loc[0]) for loc in locs))
print(' : '.join(str(x1[0] - x0[0]) for x0, x1 in zip(locs, locs[1:])))

#locs.sort()
coords_pm180 = [round(168 - 336 * r / 192 + 6) for (r, _) in locs]
coords_pm180.sort(reverse=True)
print("patrol_ys =", coords_pm180)

print(' : '.join(str(x0 - x1) for x0, x1 in zip(coords_pm180, coords_pm180[1:])))

#print(7/192, 21/360)

d32_rows = [40, 48, 57, 66, 75, 84, 93, 102, 117, 127, 137, 147, 157]
pytch_diffs = [14, 16, 16, 16, 16, 16, 16, 27, 17, 17, 17, 17]
pytch_rows = [104]
for d in pytch_diffs:
    pytch_rows.append(pytch_rows[-1] - d)

pytch_from_d32 = dict(zip(d32_rows, pytch_rows))
pytch_rows_scrambled = [pytch_from_d32[d32r] for d32r, _ in locs]
print(pytch_rows_scrambled)
