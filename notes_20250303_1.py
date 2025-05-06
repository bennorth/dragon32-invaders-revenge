import dragon32.file as DF
import sys
import numpy as np

with open(sys.argv[1], 'rb') as f_in:
    cas_bytes = np.fromfile(f_in, dtype=np.uint8)
    f = DF.File.new_from_CAS_bytes(cas_bytes)
    print(f.start_addr, f.load_addr)
    with open(sys.argv[2], 'wb') as f_out:
        f_out.write(f.data.tobytes())


