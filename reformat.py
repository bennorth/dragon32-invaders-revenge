import sys
import re
import io
from dataclasses import dataclass
from colored import Fore as CF, Back as CB, Style as CS
from bs4 import BeautifulSoup, NavigableString
from typing import Any, Set
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


def code_in_pre(ctx, code_spans):
    code = ctx.soup.new_tag("code")
    for span_cls, span_text in code_spans:
        span = ctx.soup.new_tag("span")
        span.attrs["class"] = span_cls
        if span_cls == "asm-code-operand":
            if (tgt_lbl := ctx.chunk_from_label.get(span_text)) is not None:
                a = ctx.soup.new_tag("a")
                a.attrs["href"] = f"#LBL--{tgt_lbl}"
                a.string = span_text
                span.append(a)
            elif (
                    span_text != ""
                    and span_text[0] == "#"
                    and (tgt_lbl := ctx.chunk_from_label.get(span_text[1:])) is not None
            ):
                a = ctx.soup.new_tag("a")
                a.attrs["href"] = f"#LBL--{tgt_lbl}"
                a.string = span_text[1:]
                span.append(NavigableString("#"))
                span.append(a)
            elif (
                    len(span_text) >= 2
                    and span_text[0] == "["
                    and span_text[-1] == "]"
                    and (tgt_lbl := ctx.chunk_from_label.get(span_text[1:-1])) is not None
                ):
                a = ctx.soup.new_tag("a")
                a.attrs["href"] = f"#LBL--{tgt_lbl}"
                a.string = span_text[1:-1]
                span.append(NavigableString("["))
                span.append(a)
                span.append(NavigableString("]"))
            else:
                span.string = span_text
        else:
            span.string = span_text
        code.append(span)
    pre = ctx.soup.new_tag("pre")
    pre.append(code)
    return pre


k_chunk_marker = re.compile("<(/?)(.)CHUNK>")

@dataclass
class HtmlOutputContext:
    soup: Any
    chunk_from_label: dict

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

    def img_divs(self, ctx):
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
        img = ctx.soup.new_tag("img")
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

    def first_label(self):
        if self.kind == "P":
            return # Pretend the prelude has no label
        for ln in self.lines:
            if hasattr(ln, "label") and ln.label is not None:
                return ln.label

    def populate_label_lut(self, chunk_from_label):
        if (self_label := self.first_label()) is not None:
            for ln in self.lines:
                if (ln_lbl := getattr(ln, "label", None)) is not None:
                    if ln_lbl in chunk_from_label:
                        raise ValueError(
                            f'duplicate label "{ln_lbl}"'
                            f' in chunks "{self_label}"'
                            f' and "{chunk_from_label[ln_lbl]}"'
                        )
                    chunk_from_label[ln_lbl] = self_label

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

    def html(self, ctx):
        self.maybe_reformat_data()
        div = ctx.soup.new_tag("div")
        if (id_label := self.first_label()) is not None:
            div.attrs["id"] = f"LBL--{id_label}"
        class_suffix = {
            "P": "prelude",
            "C": "code",
            "D": "data",
            "A": "directive",  # "Assembler directive"; "D" taken
            "U": "unused",
        }[self.kind]
        div.attrs["class"] = f"listing-chunk chunk-{class_suffix}"
        for div1 in self.img_divs(ctx):
            div.append(div1)
        lines_nub = self.lines[:-3] if self.ends_with_org() else self.lines
        for line in lines_nub:
            div.append(line.html(ctx))
        divs = [div]
        if self.ends_with_org():
            ch = ListingChunk("A", [self.lines[-2]])
            divs.extend(ch.html(ctx))
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

    def html(self, ctx):
        pre = code_in_pre(
            ctx,
            [
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

    def html(self, ctx):
        return code_in_pre(ctx, [])


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

    def html(self, ctx):
        return code_in_pre(
            ctx,
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

    def html(self, ctx):
        return code_in_pre(
            ctx,
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

listing_plines = [parsed(idx, line) for idx, line in enumerate(sys.stdin)]

last_lbl = "UNKNOWN"
for pline in listing_plines[-1::-1]:
    if hasattr(pline, "label") and pline.label is not None:
        last_lbl = pline.label
    if hasattr(pline, "comment") and pline.comment == "%%AUTOTITLE":
        pline.comment = last_lbl
        pline.special_kind = "h2"

all_chunks = []
open_chunk = ListingChunk("P", [])
for pline in listing_plines:
    if (mchunk := ListingChunk.maybe_from_line(pline)) is not None:
        if open_chunk is not None:
            print("=========================", pline, file=sys.stderr)
            raise ValueError("bad chunk nesting")
        open_chunk = mchunk
    elif open_chunk is not None and open_chunk.line_closes(pline):
        all_chunks.append(open_chunk)
        open_chunk = None
    else:
        if open_chunk is not None:
            open_chunk.lines.append(pline)
        else:

            print("----------------", pline, file=sys.stderr)
            raise ValueError("line outside chunk")


## Enough to give each chunk an ID?  Nearly.  Movement routines jump
## to "local" labels in one special one.  Can maybe patch that by
## hand.

if open_chunk is not None:
    all_chunks.append(open_chunk)


all_chunk_labels = set(
    [
        "MPR_L1",
        "MPR_L2",
        "PlayerData_0_b_NLives",
        "PlayerData_1_b_NLives",
        "Arr_PlayerData_1",
        "PlayerData_0_s_ScoreDisplay",
        "PlayerData_1_s_ScoreDisplay",
        "Arr_DefendersData_Loc",
        "PlayerData_0_s_TopLifeShip",
        "PlayerData_1_s_TopLifeShip",
        "MPL_MovePlayerFromKeyboard"
    ]
)

for chunk in all_chunks:
    if (chunk_lbl := chunk.first_label()) is not None:
        all_chunk_labels.add(chunk_lbl)

chunk_from_label = {}
for chunk in all_chunks:
    chunk.populate_label_lut(chunk_from_label)

ctx = HtmlOutputContext(soup, chunk_from_label)

for chunk in all_chunks:
    html_main.extend(chunk.html(ctx))


# Not "prettify()" because that inserts unwanted spaces:
print(str(soup))
