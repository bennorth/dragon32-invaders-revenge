for vel in [0x01, 0xff]:
    for xcol in range(1, 0x20):
        prod_low = (xcol * vel) % 0x100
        mark = ' **' if prod_low in [0x01, 0xe1] else ''
        print(f"{kvel:02x} {xcol:02x} {prod_low:02x}{mark}")
