import struct, math
import numpy as N
from collections import namedtuple

class BasicLine(namedtuple('_BasicLine',
                           'number text')):
    #
    Reserved_Word_from_token = {
        0x80: 'FOR',
        0x81: 'GO',
        0x82: 'REM',
        0x83: '\'',
        0x84: 'ELSE',
        0x85: 'IF',
        0x86: 'DATA',
        0x87: 'PRINT',
        0x88: 'ON',
        0x89: 'INPUT',
        0x8a: 'END',
        0x8b: 'NEXT',
        0x8c: 'DIM',
        0x8d: 'READ',
        0x8e: 'LET',
        0x8f: 'RUN',
        0x90: 'RESTORE',
        0x91: 'RETURN',
        0x92: 'STOP',
        0x93: 'POKE',
        0x94: 'CONT',
        0x95: 'LIST',
        0x96: 'CLEAR',
        0x97: 'NEW',
        0x98: 'DEF',
        0x99: 'CLOAD',
        0x9a: 'CSAVE',
        0x9b: 'OPEN',
        0x9c: 'CLOSE',
        0x9d: 'LLIST',
        0x9e: 'SET',
        0x9f: 'RESET',
        0xa0: 'CLS',
        0xa1: 'MOTOR',
        0xa2: 'SOUND',
        0xa3: 'AUDIO',
        0xa4: 'EXEC',
        0xa5: 'SKIPF',
        0xa6: 'DEL',
        0xa7: 'EDIT',
        0xa8: 'TRON',
        0xa9: 'TROFF',
        0xaa: 'LINE',
        0xab: 'PCLS',
        0xac: 'PSET',
        0xad: 'PRESET',
        0xae: 'SCREEN',
        0xaf: 'PCLEAR',
        0xb0: 'COLOR',
        0xb1: 'CIRCLE',
        0xb2: 'PAINT',
        0xb3: 'GET',
        0xb4: 'PUT',
        0xb5: 'DRAW',
        0xb6: 'PCOPY',
        0xb7: 'PMODE',
        0xb8: 'PLAY',
        0xb9: 'DLOAD',
        0xba: 'RENUM',
        0xbb: 'TAB(',
        0xbc: 'TO',
        0xbd: 'SUB',
        0xbe: 'FN',
        0xbf: 'THEN',
        0xc0: 'NOT',
        0xc1: 'STEP',
        0xc2: 'OFF',
        0xc3: '+',
        0xc4: '-',
        0xc5: '*',
        0xc6: '/',
        0xc7: '^',
        0xc8: 'AND',
        0xc9: 'OR',
        0xca: '>',
        0xcb: '=',
        0xcc: '<',
        0xcd: 'USING'}

    Function_Word_from_token = {
        0x80: 'SGN',
        0x81: 'INT',
        0x82: 'ABS',
        0x83: 'POS',
        0x84: 'RND',
        0x85: 'SQR',
        0x86: 'LOG',
        0x87: 'EXP',
        0x88: 'SIN',
        0x89: 'COS',
        0x8a: 'TAN',
        0x8b: 'ATN',
        0x8c: 'PEEK',
        0x8d: 'LEN',
        0x8e: 'STR$',
        0x8f: 'VAL',
        0x90: 'ASC',
        0x91: 'CHR$',
        0x92: 'EOF',
        0x93: 'JOYSTK',
        0x94: 'FIX',
        0x95: 'HEX$',
        0x96: 'LEFT$',
        0x97: 'RIGHT$',
        0x98: 'MID$',
        0x99: 'POINT',
        0x9a: 'INKEY$',
        0x9b: 'MEM',
        0x9c: 'VARPTR',
        0x9d: 'INSTR',
        0x9e: 'TIMER',
        0x9f: 'PPOINT',
        0xa0: 'STRING$',
        0xa1: 'USR'}

    @staticmethod
    def detokenize(ttxt):
        txt_pcs = []
        i_txt = iter(ttxt)
        for c in i_txt:
            if c == 0xff:
                f_tok = i_txt.next()
                txt_pcs.append(BasicLine.Function_Word_from_token.get(f_tok, '???'))
            elif c >= 0x80:
                txt_pcs.append(BasicLine.Reserved_Word_from_token.get(c, '???'))
            else:
                txt_pcs.append(chr(c))
        return ''.join(txt_pcs)

    @classmethod
    def new_from_number_and_tokenized_text(cls, n, ttxt):
        txt = BasicLine.detokenize(ttxt)
        return cls(n, txt)

    @staticmethod
    def pprint_lines(lines):
        max_n = max(line.number for line in lines)
        n_digits = int(math.floor(math.log10(max_n)) + 1)
        return ['%*d  %s' % (n_digits, line.number, line.text[:-1])
                for line in lines]


def next_line_from_xs(xs, addr_0):
    """
    Assuming that the BASIC code encoded as an initial segment of XS is
    to be placed at ADDR_0, return triple

        LINE, REMAINING_XS, ADDR_1

    where LINE is a BasicLine object containing the line's number and
    its de-tokenised program text, REMAINING_XS is the un-decoded
    portion of the passed-in XS, and ADDR_1 is where the next line would
    start.
    """
    txt_lb = 4
    addr_1, line_no = struct.unpack('>HH', xs[:txt_lb])
    if addr_0 == -1:
        null_idx_0 = N.where(xs[txt_lb:] == 0)[0][0]
        addr_0 = addr_1 - null_idx_0 - 5
    n_bytes_tokenized_text = addr_1 - addr_0 - 4
    #print line_no, ':', addr_0, addr_1, n_bytes_tokenized_text
    txt_ub = txt_lb + n_bytes_tokenized_text
    tokenized_text = xs[txt_lb : txt_ub]
    remaining_xs = xs[txt_ub:]
    line = BasicLine.new_from_number_and_tokenized_text(line_no,
                                                        tokenized_text)
    return line, remaining_xs, addr_1

def program_terminator_p(xs):
    return xs.size == 2 and N.all(xs == 0)

def program_lines_from_encoding(xs, addr = 0x1e01):
    lines = []
    while not program_terminator_p(xs):
        line, xs, addr = next_line_from_xs(xs, addr)
        lines.append(line)
        #if len(lines) > 70: break
    return lines
