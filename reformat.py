import sys
import re
import io
from dataclasses import dataclass
from colored import Fore as CF, Back as CB, Style as CS
from bs4 import BeautifulSoup
from typing import Any
from PIL import Image
from make_img import img_from_bytes
from base64 import b64encode

LABEL_WD = 40
INSTR_WD = 40

COMMENT_style = CS.ITALIC + CF.SEA_GREEN_2
LABEL_style = CF.ORANGE_1
INSTR_style = CF.WHITE
OPERAND_style = CF.LIGHT_CORAL
DUMP_ADDR_style = CF.STEEL_BLUE_3
DUMP_DATA_style = CF.SLATE_BLUE_3B


def code_in_pre(soup, code_spans):
    code = soup.new_tag("code")
    for span_cls, span_text in code_spans:
        span = soup.new_tag("span")
        span.attrs["class"] = span_cls
        span.string = span_text
        code.append(span)
    pre = soup.new_tag("pre")
    pre.append(code)
    return pre


k_chunk_marker = re.compile("<(/?)(.)CHUNK>")

@dataclass
class ListingChunk:
    kind: str
    lines: [Any]

    @classmethod
    def maybe_from_line(cls, pline):
        if (mkind := pline.chunk_start_kind()) is None:
            return None
        return cls(mkind, [])

    def line_closes(self, pline):
        if (mkind := pline.chunk_end_kind()) is None:
            return False
        if mkind != self.kind:
            raise ValueError(
                f"ListingChunk: opened with {self.kind} but closed with {mkind}"
            )
        return True

    def verify_kind(self, kind):
        if self.kind != kind:
            raise ValueError(f"bad chunk: open {self.kind} but close {kind}")

    def ends_with_org(self):
        return (
            isinstance(self.lines[-1], BlankLine)
            and isinstance(self.lines[-2], DirectiveLine)
            and self.lines[-2].instr == "ORG"
            and isinstance(self.lines[-3], BlankLine)
        )

    def acquire_gfx_directive(self):
        gfx_idx, gfx_n_bytes_per_row, gfx_layout = None, None, None
        for i, ln in enumerate(self.lines):
            if isinstance(ln, CommentLine) and ln.comment.startswith("%%GFX"):
                gfx_idx = i
                pcs = ln.comment.split()
                gfx_n_bytes_per_row = int(pcs[1])
                gfx_layout = pcs[2] if len(pcs) > 2 else "horizontal"
        if gfx_idx is not None:
            self.lines.pop(gfx_idx)
        return gfx_n_bytes_per_row, gfx_layout

    def code_bytes(self):
        code_bytes = []
        for ln in self.lines:
            if not isinstance(ln, CodeLine):
                continue
            for byte_hex in ln.dump_data.split("'")[0].split():
                code_bytes.append(int(byte_hex, 16))
        return code_bytes

    def img_divs(self, soup):
        m_n_bytes_per_row, img_layout = self.acquire_gfx_directive()
        if m_n_bytes_per_row is None:
            return []

        img_bytes = self.code_bytes()
        if (
            len(img_bytes) % m_n_bytes_per_row == 1
            and img_layout == "vertical"
            and img_bytes[-1] == 0xff
        ):
            # Text might have a $FF terminator
            img_bytes = img_bytes[:-1]
        if len(img_bytes) % m_n_bytes_per_row != 0:
            raise ValueError(
                f"len(img_bytes)={len(img_bytes)} not div {m_n_bytes_per_row}"
            )

        img_scale = 8 if img_layout == "horizontal" else 6
        im = img_from_bytes(img_bytes, m_n_bytes_per_row, img_layout, img_scale, green_0=True)
        png_bytesio = io.BytesIO()
        im.save(png_bytesio, "PNG")
        png_bytes = png_bytesio.getvalue()
        png_b64 = b64encode(png_bytes).decode()
        img = soup.new_tag("img")
        img.attrs["class"] = "gfx-img"
        img.attrs["src"] = "data:image/png;base64," + png_b64
        return [img]

    def acquire_reformat_data_directive(self):
        rfd_idx, rfd_n_bytes_per_row = None, None
        for i, ln in enumerate(self.lines):
            if isinstance(ln, CommentLine) and ln.comment.startswith("%%RFD"):
                rfd_idx = i
                pcs = ln.comment.split()
                rfd_n_bytes_per_row = int(pcs[1])
        if rfd_idx is not None:
            self.lines.pop(rfd_idx)
        return rfd_n_bytes_per_row

    def first_code(self):
        for ln in self.lines:
            if isinstance(ln, CodeLine):
                return ln

    def maybe_reformat_data(self):
        if (n_bytes_per_row := self.acquire_reformat_data_directive()) is None:
            return
        cbytes = self.code_bytes()
        new_lines = []
        first = True
        addr = int(self.first_code().dump_addr, 16)
        for idx0 in range(0, len(cbytes), n_bytes_per_row):
            row_bytes = cbytes[idx0:idx0+n_bytes_per_row]
            row_chrs = [chr(b) for b in row_bytes]
            hexs_dump = "'.....'"
            hexs = ",".join(f"${b:02X}" for b in row_bytes)
            hexs_dump = " ".join(f"{b:02X}" for b in row_bytes)
            chrs_dump = "".join(ch if (ord(ch) < 0x80 and ch.isprintable()) else "." for ch in row_chrs)
            hex_wd = max(n_bytes_per_row * 3, 13)
            full_dump = f"{hexs_dump:{hex_wd}}  '{chrs_dump}'"
            new_line = CodeLine(
                -1,
                self.first_code().label if first else None,
                "FCB",
                hexs,
                f"{addr:04X}",
                full_dump
            )
            addr += n_bytes_per_row
            new_lines.append(new_line)
            first = False

        all_new_lines = []
        lines_iter = iter(self.lines)
        for ln in lines_iter:
            if not isinstance(ln, CodeLine):
                all_new_lines.append(ln)
            else:
                all_new_lines.extend(new_lines)
                for ln in lines_iter:
                    if not isinstance(ln, CodeLine):
                        all_new_lines.append(ln)
                        break

        self.lines = all_new_lines

    def html(self, soup):
        self.maybe_reformat_data()
        div = soup.new_tag("div")
        class_suffix = {
            "C": "code",
            "D": "data",
            "A": "directive",  # "Assembler directive"; "D" taken
            "U": "unused",
        }[self.kind]
        div.attrs["class"] = f"listing-chunk chunk-{class_suffix}"
        for div1 in self.img_divs(soup):
            div.append(div1)
        lines_nub = self.lines[:-3] if self.ends_with_org() else self.lines
        for line in lines_nub:
            div.append(line.html(soup))
        divs = [div]
        if self.ends_with_org():
            ch = ListingChunk("A", [self.lines[-2]])
            divs.extend(ch.html(soup))
        return divs


class DoesNotMarkChunks:
    def chunk_start_kind(self):
        return None

    def chunk_end_kind(self):
        return None


@dataclass
class CommentLine:
    source_idx: int
    comment: str
    special_kind: (str | None)

    @classmethod
    def from_line(cls, idx, line):
        if not line.startswith(";"):
            raise ValueError(f"line '{line}' not comment")
        if line[1] == " ":
            line = line[2:]
        raw_comment = line.rstrip()
        if raw_comment == ";;":
            return cls(idx, "", None)
        else:
            return cls(idx, raw_comment, None)

    def pretty(self):
        return f"{'':{LABEL_WD}}{COMMENT_style}; {self.comment}{CS.reset}"

    def html(self, soup):
        pre = code_in_pre(
            soup, [
                ("asm-comment-intro", ";"),
                ("asm-comment", self.comment),
            ]
        )
        match self.special_kind:
            case None:
                pass
            case "h2":
                pre.attrs["class"] = "chunk-h2"
        return pre

    def chunk_start_kind(self):
        if (m := k_chunk_marker.match(self.comment)) is None:
            return None
        if m.group(1) == "/":
            return None
        return m.group(2)

    def chunk_end_kind(self):
        if (m := k_chunk_marker.match(self.comment)) is None:
            return None
        if m.group(1) == "":
            return None
        return m.group(2)


@dataclass
class BlankLine(DoesNotMarkChunks):
    source_idx: int

    def pretty(self):
        return ""

    def html(self, soup):
        return code_in_pre(soup, [])


@dataclass
class DirectiveLine(DoesNotMarkChunks):
    source_idx: int
    label: str | None
    instr: str
    operand: str | None

    @classmethod
    def from_line(cls, idx, line):
        parts = line.rstrip().split()
        if line.startswith(" "):
            op = parts[1] if len(parts) > 1 else None
            return cls(idx, None, parts[0], op)
        else:
            return cls(idx, *parts)

    def pretty(self):
        lbl = self.label or ""
        op = self.operand or ""
        full_instr = f"{INSTR_style}{self.instr:4} {OPERAND_style}{op:{INSTR_WD}}"
        return f"{LABEL_style}{(lbl):>{LABEL_WD}}  {full_instr}"

    def html(self, soup):
        return code_in_pre(
            soup,
            [
                ("asm-directive-label", self.label or ""),
                ("asm-directive-instr", self.instr),
                ("asm-directive-operand", self.operand or ""),
            ]
        )


@dataclass
class CodeLine(DoesNotMarkChunks):
    source_idx: int
    label: str | None
    instr: str
    operand: str | None
    dump_addr: str
    dump_data: str

    @classmethod
    def from_line(cls, idx, line):
        parts = line.strip().split(";")
        dump_addr, dump_data = parts[1].split(":", 1)
        dump_data = dump_data.strip()
        if line.startswith(" "):
            parts1 = parts[0].strip().split(None, 1)
            op = parts1[1] if len(parts1) > 1 else None
            return cls(idx, None, parts1[0], op, dump_addr, dump_data)
        else:
            parts1 = parts[0].strip().split(None, 2)
            op = parts1[2] if len(parts1) > 2 else None
            return cls(idx, parts1[0], parts1[1], op, dump_addr, dump_data)

    def pretty(self):
        lbl = self.label or ""
        op = self.operand or ""
        full_instr = f"{INSTR_style}{self.instr:4} {OPERAND_style}{op:{INSTR_WD}}"
        dump = f"{DUMP_ADDR_style}{self.dump_addr}: {DUMP_DATA_style}{self.dump_data}"
        return f"{LABEL_style}{(lbl):>{LABEL_WD}}  {full_instr} {dump}"

    def html(self, soup):
        return code_in_pre(
            soup,
            [
                ("asm-code-label", self.label or ""),
                ("asm-code-instr", self.instr),
                ("asm-code-operand", self.operand or ""),
                ("asm-code-dump-addr", self.dump_addr),
                ("asm-code-dump-data", self.dump_data),
            ]
        )


def parsed(idx, line):
    if not line.strip():
        return BlankLine(idx)
    elif line.startswith(";"):
        return CommentLine.from_line(idx, line)
    elif ";" not in line:
        return DirectiveLine.from_line(idx, line)
    else:
        return CodeLine.from_line(idx, line)


html_template = open("rendered-asm/template.html", "rt").read()
soup = BeautifulSoup(html_template, "html.parser")
html_main = soup.body.main

all_labels = []
open_chunk = None

listing_plines = [parsed(idx, line) for idx, line in enumerate(sys.stdin)]

last_lbl = "UNKNOWN"
for pline in listing_plines[-1::-1]:
    if hasattr(pline, "label") and pline.label is not None:
        last_lbl = pline.label
    if hasattr(pline, "comment") and pline.comment == "%%AUTOTITLE":
        pline.comment = last_lbl
        pline.special_kind = "h2"

for pline in listing_plines:
    if hasattr(pline, "label"):
        lbl = pline.label
        if lbl is not None:
            all_labels.append(lbl)

    if (mchunk := ListingChunk.maybe_from_line(pline)) is not None:
        if open_chunk is not None:
            print("=========================", pline, file=sys.stderr)
            raise ValueError("bad chunk nesting")
        open_chunk = mchunk
    elif open_chunk is not None and open_chunk.line_closes(pline):
        html_main.extend(open_chunk.html(soup))
        open_chunk = None
    else:
        if open_chunk is not None:
            open_chunk.lines.append(pline)
        else:
            html_main.append(pline.html(soup))

    #print(pline.pretty())

if open_chunk is not None:
    html_main.extend(open_chunk.html(soup))


# Not "prettify()" because that inserts unwanted spaces:
print(str(soup))
