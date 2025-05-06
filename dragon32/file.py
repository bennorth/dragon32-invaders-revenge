from collections import namedtuple
import wave, re
import numpy as N
from dragon32.filter import periods_from_pzcs

def samples_from_fname(fname):
    wave_file = wave.open(fname)
    all_xs = wave_file.readframes(wave_file.getnframes())
    xs_l = N.fromstring(all_xs[::2], dtype = N.uint8).astype(N.float32)
    xs_r = N.fromstring(all_xs[1::2], dtype = N.uint8).astype(N.float32)
    return 0.5 * (xs_l + xs_r)

def samples_from_fname_s16le(fname):
    wave_file = wave.open(fname)
    all_xs = wave_file.readframes(wave_file.getnframes())
    all_xs_float = N.fromstring(all_xs, dtype = N.int16).astype(N.float32) / 32768.0
    xs_l = all_xs_float[::2]
    xs_r = all_xs_float[1::2]
    return 0.5 * (xs_l + xs_r)

SAMPLES_PER_SECOND = 48000
def nsamples_from_timespec(s):
    """
    E.g.,
        012345678
        04:23.887
    """

    mm, ss, th = map(int, (s[:2], s[3:5], s[6:]))
    seconds = mm * 60.0 + ss + th * 0.001
    return int(seconds * SAMPLES_PER_SECOND)

def extract_interval(xs, time_lb, time_ub):
    return xs[nsamples_from_timespec(time_lb) : nsamples_from_timespec(time_ub)]

# NB: discarded by re-definition below.
def lowpass_filter(xs):
    ys = N.zeros_like(xs)
    for n in range(3, len(xs)):
        ys[n] = (xs[n- 3]
                 + 3 * xs[n- 2]
                 + 3 * xs[n- 1]
                 + xs[n]
                 + (  0.5610236032 * ys[n- 3])
                 + ( -2.0052068771 * ys[n- 2])
                 + (  2.4259180679 * ys[n- 1]))
    fxs = (ys - N.mean(ys)) / N.std(ys)
    return fxs

def bandpass_filter_600_2400(xs):
    if xs.ndim != 1:
        raise ValueError('only 1-dimensional arrays supported')

    ys = N.zeros_like(xs)

    code = """
        int n = Nxs[0];
        for (int i = 6; i < n; ++i)
        {
            ys[i] = (( -xs[i-6])
                    + (  3 * xs[i- 4])
                    + (  -3 * xs[i- 2])
                    + (  xs[i- 0])
                    + ( -0.6235385946 * ys[i- 6])
                    + (  3.9845339514 * ys[i- 5])
                    + (-10.6773041974 * ys[i- 4])
                    + ( 15.3567871865 * ys[i- 3])
                    + (-12.5018997447 * ys[i- 2])
                    + (  5.4614094447 * ys[i- 1]));
        }"""

    WEAVE.inline(code, ['xs', 'ys'])

    fxs = (ys - N.mean(ys)) / N.std(ys)
    return fxs

def bandpass_filter_300_4800(xs):
    if xs.ndim != 1:
        raise ValueError('only 1-dimensional arrays supported')

    ys = N.zeros_like(xs)

    code = """
        int n = Nxs[0];
        for (int i = 6; i < n; ++i)
        {
            ys[i] = (( -xs[i-6])
                    + (  3 * xs[i- 4])
                    + (  -3 * xs[i- 2])
                    + (  xs[i- 0])
                    + ( -0.3021101849 * ys[i- 6])
                    + (  2.1396838728 * ys[i- 5])
                    + ( -6.3921156590 * ys[i- 4])
                    + ( 10.3486538488 * ys[i- 3])
                    + ( -9.5687341134 * ys[i- 2])
                    + (  4.7746132669 * ys[i- 1]));
        }"""

    WEAVE.inline(code, ['xs', 'ys'])

    fxs = (ys - N.mean(ys)) / N.std(ys)
    return fxs


def cycle_periods(xs, tgt_diff = -1.0):
    sxs = N.where(xs > 0.0, 1.0, 0.0)
    pgzxs = N.where(N.diff(sxs) == tgt_diff)[0]  # Depends on phase reponse of filter
    return N.diff(pgzxs)

def next_data_bits(bs_txt, leader_p = False):
    """
    Return pair

        BITS_DATA_STARTING_AFTER_SYNC_BYTE,
        BITS_TEXT_STARTING_AFTER_SYNC_BYTE
    """
    m = (re.search('(10){50}.{,10}10101000111100', bs_txt) if leader_p
         else re.match('.{,10}10101000111100', bs_txt))
    if m is None:
        raise ValueError('leader byte(s) and sync byte not found: %s' % bs_txt[:200])

    m_end = m.end()
    block_bits = N.fromstring(bs_txt[m_end:], dtype = N.uint8) - 48
    return block_bits, bs_txt[m_end:]

def bytes_from_bits(bs):
    n_whole_bytes = (bs.size / 8)
    bs = bs[:(n_whole_bytes * 8)].reshape((n_whole_bytes, 8))
    bit_vals = N.power(2, range(8)).astype(N.uint8)
    block_bytes = N.sum(bs * bit_vals, axis = 1).astype(N.uint8)
    return block_bytes

class Block(namedtuple('_Block',
                       'type data raw_bytes')):
    # Block types
    BT_NAMEFILE, BT_DATA, BT_END_OF_FILE = range(3)
    btype_from_byte = {0x01: BT_DATA,
                       0xff: BT_END_OF_FILE,
                       0x00: BT_NAMEFILE}

    @classmethod
    def new_from_bytes(cls, bytes, diag_tag = ''):
        b_type = cls.btype_from_byte[bytes[0]]
        b_len = bytes[1]
        b_data = bytes[2 : 2 + b_len]
        b_chk = bytes[2 + b_len]

        chk = N.sum(bytes[: 2 + b_len]).astype(N.uint8)
        if b_chk != chk:
#             raise ValueError('recorded chksum 0x%02x but calcd 0x%02x'
#                              % (b_chk, chk))
            print ('WARNING: recorded chksum 0x%02x but calcd 0x%02x [%s]'
                   % (b_chk, chk, diag_tag))

        if b_type == cls.BT_NAMEFILE:
            if b_len != 15:
                # print ' '.join('%02x' % x for x in bytes)
                # print ''.join('%c' % x for x in bytes[:10])
                raise ValueError('namefile block must have len 15, not %d'
                                 % b_len)

        return cls(b_type, b_data, N.array(bytes[:3+b_len]))

    @property
    def data_len(self):
        return len(self.data)

    def as_full_bytes(self, leader_p):
        def B(xs): return N.array(xs, dtype = N.uint8)
        leader_bytes = B([])
        if leader_p:
            leader_bytes = N.zeros((128,), dtype = N.uint8)
            leader_bytes[:] = 0x55
        sync_bytes = B([0x55, 0x3c])
        trailer_byte = B([0x55])
        return N.concatenate((leader_bytes, sync_bytes, self.raw_bytes, trailer_byte))

    @staticmethod
    def bytestream(blocks):
        gapped_p = blocks[0].data[10] == 0xff
        block_bytes = ([blocks[0].as_full_bytes(True),
                        blocks[1].as_full_bytes(True)]
                       + [b.as_full_bytes(gapped_p) for b in blocks[2:]])
        return N.concatenate(tuple(block_bytes))


class File(namedtuple('_File',
                      'name type storage gapped start_addr load_addr data blocks')):
    # File types
    FT_BASIC, FT_DATA, FT_MACHINE_CODE = range(3)
    ftype_from_byte = {0x00: FT_BASIC,
                       0x01: FT_DATA,
                       0x02: FT_MACHINE_CODE}

    label_from_type = {FT_BASIC: 'BASIC',
                       FT_DATA: 'DATA',
                       FT_MACHINE_CODE: 'MACHINE-CODE'}

    def pprint_str(self):
        return ('"%s": %d bytes; type %s; storage 0x%02x;'
                ' gapped 0x%02x; start 0x%04x; load 0x%04x'
                % (self.name, self.data.size,
                   self.label_from_type[self.type],
                   self.storage, self.gapped,
                   self.start_addr, self.load_addr))

    @classmethod
    def new_from_blocks(cls, blks):
        namefile_blk = blks[0]
        if namefile_blk.type != Block.BT_NAMEFILE:
            raise ValueError('blks[0] must be namefile block')

        nf_data = namefile_blk.data
        f_name = nf_data[:8].astype(N.uint8).tostring()
        f_type = cls.ftype_from_byte[nf_data[8]]
        f_storage = int(nf_data[9])
        f_gapped = int(nf_data[10])
        f_start_addr = int(nf_data[11] * 256 + nf_data[12])
        f_load_addr = int(nf_data[13] * 256 + nf_data[14])

        f_data_pcs = []
        for im1, blk in enumerate(blks[1:-1]):
            if blk.type != Block.BT_DATA:
                raise ValueError('block %d not BT_DATA block' % (im1 + 1))
            f_data_pcs.append(blk.data)

        if blks[-1].type != Block.BT_END_OF_FILE:
            raise ValueError('final block not BT_END_OF_FILE')

        f_data = N.concatenate(f_data_pcs).astype(N.uint8)

        return cls(f_name,
                   f_type,
                   f_storage,
                   f_gapped,
                   f_start_addr,
                   f_load_addr,
                   f_data,
                   blks)

    @classmethod
    def new_from_samples(cls, xs, prefiltered_p = False, tgt_diff = -1.0):
        if prefiltered_p:
            fxs = xs
        else:
            fxs = lowpass_filter(xs)
            fxs = bandpass_filter_600_2400(xs)
        #ps = cycle_periods(fxs, tgt_diff)
        ps = periods_from_pzcs(fxs)
        bs = N.where(ps > 33, 0, 1).astype(N.uint8)

        # HEM HEM:
        bs_txt = N.where(bs, 49, 48).astype(N.uint8).tostring()

#         print bs_txt

        block_bits, block_bits_txt = next_data_bits(bs_txt, leader_p = True)
        block_bytes = bytes_from_bits(block_bits)
        blks = [Block.new_from_bytes(block_bytes, 'leader-0')]
#        print bs_txt
        # print 'first block'
        # print list(blks[0].raw_bytes)
        # print list(blks[0].data)
        # print blks[-1]
        bs_txt = block_bits_txt[(blks[-1].data_len + 4) * 8:]

        gapped_p = blks[0].data[10] == 0xff

        # print 'about to try to get second block from:'
        # print bs_txt

        block_bits, block_bits_txt = next_data_bits(bs_txt, leader_p = True)
        block_bytes = bytes_from_bits(block_bits)
        blks.append(Block.new_from_bytes(block_bytes, 'leader-1'))
        # print 'second block'
        # print block_bytes
        # print blks[-1]
        bs_txt = block_bits_txt[(blks[-1].data_len + 4) * 8:]

        idx = 0
        while True:
            block_bits, block_bits_txt = next_data_bits(bs_txt, leader_p = gapped_p)
            block_bytes = bytes_from_bits(block_bits)
            blks.append(Block.new_from_bytes(block_bytes, 'data-%d' % idx))
            idx += 1
#             print bs_txt
#             print block_bytes
#             print blks[-1]
            bs_txt = block_bits_txt[(blks[-1].data_len + 4) * 8:]
#             print bs_txt
            if blks[-1].type == Block.BT_END_OF_FILE:
                break

        return cls.new_from_blocks(blks)

    @staticmethod
    def next_block_bytes(bytes):
        """Return pair

            Bytes of first block (without leader (if any) and sync bytes)
            Remaining bytes after first block
        """
        if len(bytes) == 0:
            raise ValueError("empty bytes")
        idx_0 = 0
        while bytes[idx_0] == 0x55:
            idx_0 += 1
        if bytes[idx_0] != 0x3c:
            raise ValueError("no sync byte")
        idx_0 += 1
        block_len = int(bytes[idx_0 + 1]);
        # In addition to the block data, there are also:
        #     block-type, block-len, [data,] checksum
        # bytes.  The trailer byte (0x55) is on the tape but is
        # omitted from the CAS format.
        idx_1 = idx_0 + block_len + 3
        return bytes[idx_0:idx_1].astype(N.uint32), bytes[idx_1:]

    @classmethod
    def new_from_CAS_bytes(cls, bytes):
        blks = []
        while len(bytes):
            block_bytes, bytes = cls.next_block_bytes(bytes)
            blks.append(Block.new_from_bytes(block_bytes))

        return cls.new_from_blocks(blks)
