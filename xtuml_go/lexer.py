"""Small lexer used by the educational xtUML subset parser."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    column: int

SYMBOLS = set("{}():=,+-#~[]<>")

def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    i, line, col = 0, 1, 1
    while i < len(source):
        ch = source[i]
        if ch in " \t\r":
            i += 1; col += 1; continue
        if ch == "\n":
            tokens.append(Token("NEWLINE", "\\n", line, col))
            i += 1; line += 1; col = 1; continue
        if source.startswith("//", i) or ch == "'":
            while i < len(source) and source[i] != "\n":
                i += 1; col += 1
            continue
        if ch == "@":
            start, start_col = i, col
            i += 1; col += 1
            while i < len(source) and (source[i].isalnum() or source[i] in "_-"):
                i += 1; col += 1
            tokens.append(Token("DIRECTIVE", source[start:i], line, start_col))
            continue
        if source.startswith("->", i):
            tokens.append(Token("REL", "->", line, col))
            i += 2; col += 2; continue
        if ch == "." and i + 1 < len(source) and source[i+1] == ".":
            tokens.append(Token("REL", "..", line, col))
            i += 2; col += 2; continue
        if ch in SYMBOLS:
            tokens.append(Token(ch, ch, line, col))
            i += 1; col += 1; continue
        start, start_col = i, col
        while i < len(source) and source[i] not in " \t\r\n" and source[i] not in SYMBOLS and source[i] != "'":
            if source.startswith("//", i):
                break
            i += 1; col += 1
        if i == start:
            raise SyntaxError(f"Baris {line}, kolom {col}: karakter tidak dikenal {ch!r}.")
        value = source[start:i]
        kind = "IDENT"
        if value.lower() in {"class", "abstract", "state_machine", "state", "initial", "transition", "action", "extends", "package", "as", "association"}:
            kind = value.upper()
        tokens.append(Token(kind, value, line, start_col))
    tokens.append(Token("EOF", "", line, col))
    return tokens
