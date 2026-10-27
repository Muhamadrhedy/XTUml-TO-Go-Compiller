"""Recursive-descent parser for a documented, intentionally limited UML/xtUML syntax."""
from .lexer import tokenize, Token
from .model import Model, UMLClass, Attribute, Operation, Parameter, StateMachine, State, Transition, Association

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, source: str):
        self.tokens = tokenize(source)
        self.i = 0
        self.model = Model()

    @property
    def current(self) -> Token:
        return self.tokens[self.i]

    def advance(self) -> Token:
        t = self.current
        if t.kind != "EOF": self.i += 1
        return t

    def accept(self, kind: str):
        if self.current.kind == kind:
            return self.advance()
        return None

    def expect(self, kind: str, message: str = "") -> Token:
        token = self.accept(kind)
        if token is None:
            t = self.current
            raise ParseError(f"Baris {t.line}, kolom {t.column}: {message or ('diharapkan ' + kind + ', ditemukan ' + repr(t.value))}")
        return token

    def skip_newlines(self):
        while self.accept("NEWLINE"): pass

    def read_name(self) -> str:
        return self.expect("IDENT", "diharapkan nama identifier").value

    def read_type(self) -> str:
        name = self.read_name()
        if self.accept("["):
            self.expect("]", "diharapkan ']' setelah '['")
            name += "[]"
        elif name in ("List", "Optional") and self.accept("<"):
            inner = self.read_type()
            self.expect(">", "diharapkan '>' pada tipe generik")
            name += f"<{inner}>"
        return name

    def parse(self) -> Model:
        self.skip_newlines()
        while self.current.kind != "EOF":
            if self.current.kind == "DIRECTIVE":
                self.advance(); self.skip_newlines(); continue
            if self.current.kind in ("PACKAGE", "TITLE"):
                self.advance()
                if self.current.kind not in ("NEWLINE", "EOF"): self.advance()
                self.skip_newlines(); continue
            if self.current.kind == "ABSTRACT":
                self.advance()
                self.expect("CLASS", "abstract harus diikuti class")
                self.parse_class()
            elif self.current.kind == "CLASS":
                self.advance(); self.parse_class()
            elif self.current.kind == "STATE_MACHINE":
                self.advance(); self.parse_state_machine()
            elif self.current.kind == "ASSOCIATION":
                self.advance(); self.parse_association()
            elif self.current.kind == "NEWLINE":
                self.skip_newlines()
            else:
                t = self.current
                # Relationship lines are retained as warnings, not silently treated as compiled behavior.
                if t.kind == "IDENT" and t.value in ("association", "relationship"):
                    while self.current.kind not in ("NEWLINE", "EOF"): self.advance()
                    self.model.warnings.append(f"Baris {t.line}: deklarasi relasi eksplisit diabaikan pada versi ini.")
                    self.skip_newlines()
                else:
                    raise ParseError(f"Baris {t.line}, kolom {t.column}: deklarasi tidak dikenal {t.value!r}.")
        if not self.model.classes:
            raise ParseError("Model tidak berisi class. Tambahkan minimal 'class Nama { ... }'.")
        return self.model

    def parse_class(self):
        name = self.read_name()
        parent = None
        if self.accept("EXTENDS"):
            parent = self.read_name()
        self.expect("{", "diharapkan '{' setelah deklarasi class")
        cls = UMLClass(name=name, parent=parent)
        self.model.classes.append(cls)
        self.skip_newlines()
        while self.current.kind not in ("}", "EOF"):
            visibility = "+"
            if self.current.kind in ("+", "-", "#", "~"):
                visibility = self.advance().value
            member_name = self.read_name()
            if self.accept(":"):
                type_name = self.read_type()
                default = None
                if self.accept("="):
                    pieces = []
                    while self.current.kind not in ("NEWLINE", "}", "EOF"):
                        pieces.append(self.advance().value)
                    default = "".join(pieces).strip()
                cls.attributes.append(Attribute(member_name, type_name, visibility, default))
            elif self.accept("("):
                params = []
                if self.current.kind != ")":
                    while True:
                        pname = self.read_name()
                        self.expect(":", "parameter harus memakai format nama: Tipe")
                        ptype = self.read_type()
                        params.append(Parameter(pname, ptype))
                        if not self.accept(","): break
                self.expect(")", "diharapkan ')' setelah parameter")
                return_type = None
                if self.accept(":"): return_type = self.read_type()
                cls.operations.append(Operation(member_name, params, return_type, visibility))
            else:
                t = self.current
                raise ParseError(f"Baris {t.line}, kolom {t.column}: member '{member_name}' harus berupa atribut ': Tipe' atau operasi '(...)'.")
            if self.current.kind not in ("NEWLINE", "}", "EOF"):
                t = self.current
                raise ParseError(f"Baris {t.line}, kolom {t.column}: token tambahan {t.value!r} pada member.")
            self.skip_newlines()
        self.expect("}", "class belum ditutup dengan '}'")
        self.skip_newlines()

    def parse_association(self):
        # DSL: association Student courses Course many
        # multiplicity: one | optional | many
        line_token = self.tokens[self.i - 1]
        source = self.read_name()
        field_name = self.read_name()
        target = self.read_name()
        multiplicity = self.read_name()
        if multiplicity not in ("one", "optional", "many"):
            raise ParseError(
                f"Baris {line_token.line}: multiplicity harus one, optional, atau many; ditemukan '{multiplicity}'."
            )
        self.model.associations.append(Association(source, field_name, target, multiplicity))
        if self.current.kind not in ("NEWLINE", "EOF"):
            t = self.current
            raise ParseError(f"Baris {t.line}, kolom {t.column}: token tambahan {t.value!r} pada association.")
        self.skip_newlines()

    def parse_state_machine(self):
        # DSL:
        # state_machine OrderLifecycle for Order {
        #   initial Pending
        #   state Pending
        #   transition Pending on Pay -> Paid action MarkPaid
        # }
        name = self.read_name()
        owner = None
        if self.current.kind == "IDENT" and self.current.value == "for":
            self.advance(); owner = self.read_name()
        self.expect("{", "diharapkan '{' setelah state_machine")
        self.skip_newlines()
        initial = None
        states, transitions = [], []
        while self.current.kind not in ("}", "EOF"):
            if self.accept("INITIAL"):
                initial = self.read_name()
            elif self.accept("STATE"):
                states.append(State(self.read_name()))
            elif self.accept("TRANSITION"):
                source = self.read_name()
                self.expect("IDENT", "diharapkan kata 'on' setelah state asal")
                # previous token's value is not enough to validate, inspect it directly via consumed token below
                # This grammar intentionally accepts 'on' as an identifier.
                event = self.read_name()
                self.expect("REL", "diharapkan '->' pada transition")
                target = self.read_name()
                action = None
                if self.accept("ACTION"): action = self.read_name()
                transitions.append(Transition(source, event, target, action))
            else:
                t = self.current
                raise ParseError(f"Baris {t.line}, kolom {t.column}: isi state machine tidak dikenal {t.value!r}.")
            if self.current.kind not in ("NEWLINE", "}", "EOF"):
                t = self.current
                raise ParseError(f"Baris {t.line}, kolom {t.column}: token tambahan {t.value!r} pada state machine.")
            self.skip_newlines()
        self.expect("}", "state machine belum ditutup")
        self.skip_newlines()
        if not owner:
            raise ParseError(f"State machine '{name}' harus menyebut pemilik: state_machine {name} for NamaClass {{")
        cls = next((c for c in self.model.classes if c.name == owner), None)
        if cls is None:
            raise ParseError(f"State machine '{name}' merujuk class '{owner}' yang belum dideklarasikan. Deklarasikan class lebih dulu.")
        if cls.state_machine:
            raise ParseError(f"Class '{owner}' sudah memiliki state machine.")
        cls.state_machine = StateMachine(name, initial or "", states, transitions)

def parse(source: str) -> Model:
    return Parser(source).parse()
