import sys
import re
from dataclasses import dataclass
from colored import Fore as CF, Back as CB, Style as CS
from bs4 import BeautifulSoup
from typing import Any

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

    def html(self, soup):
        div = soup.new_tag("div")
        class_suffix = {
            "C": "code",
            "D": "data",
            "A": "directive",  # "Assembler directive"; "D" taken
            "U": "unused",
        }[self.kind]
        div.attrs["class"] = f"listing-chunk chunk-{class_suffix}"
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
