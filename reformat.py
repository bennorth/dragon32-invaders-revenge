import sys
from dataclasses import dataclass
from colored import Fore as CF, Back as CB, Style as CS

LABEL_WD = 40
INSTR_WD = 40

COMMENT_style = CS.ITALIC + CF.SEA_GREEN_2
LABEL_style = CF.ORANGE_1
INSTR_style = CF.WHITE
OPERAND_style = CF.LIGHT_CORAL
DUMP_ADDR_style = CF.STEEL_BLUE_3
DUMP_DATA_style = CF.SLATE_BLUE_3B

@dataclass
class CommentLine:
    comment: str

    @classmethod
    def from_line(cls, line):
        if not line.startswith(";"):
            raise ValueError(f"line '{line}' not comment")
        if line[1] == " ":
            line = line[2:]
        raw_comment = line.rstrip()
        if raw_comment == ";;":
            return cls("")
        else:
            return cls(raw_comment)

    def pretty(self):
        return f"{'':{LABEL_WD}}{COMMENT_style}; {self.comment}{CS.reset}"


@dataclass
class BlankLine:
    def pretty(self):
        return ""


@dataclass
class DirectiveLine:
    label: str | None
    instr: str
    operand: str | None

    @classmethod
    def from_line(cls, line):
        parts = line.rstrip().split()
        if line.startswith(" "):
            op = parts[1] if len(parts) > 1 else None
            return cls(None, parts[0], op)
        else:
            return cls(*parts)

    def pretty(self):
        lbl = self.label or ""
        op = self.operand or ""
        full_instr = f"{INSTR_style}{self.instr:4} {OPERAND_style}{op:{INSTR_WD}}"
        return f"{LABEL_style}{(lbl):>{LABEL_WD}}  {full_instr}"


@dataclass
class CodeLine:
    label: str | None
    instr: str
    operand: str | None
    dump_addr: str
    dump_data: str

    @classmethod
    def from_line(cls, line):
        parts = line.strip().split(";")
        dump_addr, dump_data = parts[1].split(":", 1)
        dump_data = dump_data.strip()
        if line.startswith(" "):
            parts1 = parts[0].strip().split(None, 1)
            op = parts1[1] if len(parts1) > 1 else None
            return cls(None, parts1[0], op, dump_addr, dump_data)
        else:
            parts1 = parts[0].strip().split(None, 2)
            op = parts1[2] if len(parts1) > 2 else None
            return cls(parts1[0], parts1[1], op, dump_addr, dump_data)

    def pretty(self):
        lbl = self.label or ""
        op = self.operand or ""
        full_instr = f"{INSTR_style}{self.instr:4} {OPERAND_style}{op:{INSTR_WD}}"
        dump = f"{DUMP_ADDR_style}{self.dump_addr}: {DUMP_DATA_style}{self.dump_data}"
        return f"{LABEL_style}{(lbl):>{LABEL_WD}}  {full_instr} {dump}"


def parsed(line):
    if not line.strip():
        return BlankLine()
    elif line.startswith(";"):
        return CommentLine.from_line(line)
    elif ";" not in line:
        return DirectiveLine.from_line(line)
    else:
        return CodeLine.from_line(line)


all_labels = []
for line in sys.stdin:
    pline = parsed(line)
    if hasattr(pline, "label"):
        lbl = pline.label
        if lbl is not None:
            all_labels.append(lbl)
    print(pline.pretty())
