import dragon32.file as F
import dragon32.filter as FILT
import dragon32.basic as DB

def extract(xs, t0, t1, fname_nub):
    dxs = F.extract_interval(xs, t0, t1)
    ys = FILT.filter(dxs, peak = 2600.0, high_zero = 3600.0)

    f = F.File.new_from_samples(-ys, prefiltered_p = True)
    print f.pprint_str()

    def full_fname(sfx): return fname_nub + sfx

    with file(full_fname('.cas'), 'w') as f_out:
        f_out.write(F.Block.bytestream(f.blocks))

    if f.type == F.File.FT_BASIC:
        with file(full_fname('.asc'), 'w') as f_out:
            if f.storage == 0:
                prog = DB.program_lines_from_encoding(f.data, -1)
                prog_text = '\n'.join(DB.BasicLine.pprint_lines(prog) + [''])
            else:
                prog_text = f.data.tostring().replace('\r', '\n')
            f_out.write(prog_text)
    #
    elif f.type == F.File.FT_MACHINE_CODE:
        with file(full_fname('.bin'), 'w') as f_out:
            f_out.write(f.data)
    #
    else:
        print 'UNHANDLED TYPE'
