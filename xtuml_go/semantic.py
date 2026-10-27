"""Semantic validation and type normalization."""
import re
from .model import Model

TYPE_MAP = {
    "String": "string", "string": "string",
    "Integer": "int", "Int": "int", "int": "int",
    "Boolean": "bool", "bool": "bool",
    "Float": "float64", "Double": "float64", "float64": "float64",
    "Float32": "float32", "float32": "float32",
    "Long": "int64", "int64": "int64",
    "ID": "string", "Date": "time.Time", "Time": "time.Time",
    "Void": "", "void": "",
}

class SemanticError(Exception):
    pass

def go_type(type_name: str) -> str:
    if type_name.endswith("[]"):
        return "[]" + go_type(type_name[:-2])
    if type_name.startswith("List<") and type_name.endswith(">"):
        return "[]" + go_type(type_name[5:-1])
    if type_name.startswith("Optional<") and type_name.endswith(">"):
        return "*" + go_type(type_name[9:-1])
    return TYPE_MAP.get(type_name, type_name)

def exported(name: str) -> str:
    parts = re.split(r"[_\-\s]+", name)
    return "".join(p[:1].upper() + p[1:] for p in parts if p)

def private(name: str) -> str:
    parts = re.split(r"[_\-\s]+", name)
    if len(parts) <= 1: return name[:1].lower() + name[1:]
    return parts[0][:1].lower() + parts[0][1:] + "".join(p[:1].upper() + p[1:] for p in parts[1:] if p)

def validate(model: Model) -> list[str]:
    errors, warnings = [], list(model.warnings)
    names = [c.name for c in model.classes]
    if len(names) != len(set(names)):
        errors.append("Nama class duplikat ditemukan.")
    class_map = {c.name: c for c in model.classes}
    reserved = {"break","default","func","interface","select","case","defer","go","map","struct","chan","else","goto","package","switch","const","fallthrough","if","range","type","continue","for","import","return","var"}
    for cls in model.classes:
        if not re.match(r"^[A-Za-z_]\w*$", cls.name) or cls.name in reserved:
            errors.append(f"Nama class '{cls.name}' bukan identifier Go yang valid.")
        if cls.parent:
            if cls.parent not in class_map:
                errors.append(f"Class '{cls.name}' mewarisi class yang tidak ada: '{cls.parent}'.")
            if cls.parent == cls.name:
                errors.append(f"Class '{cls.name}' tidak boleh mewarisi dirinya sendiri.")
        member_names = [a.name for a in cls.attributes]
        if len(member_names) != len(set(member_names)):
            errors.append(f"Class '{cls.name}' memiliki atribut duplikat.")
        op_signatures = [(o.name, tuple((p.name,p.type_name) for p in o.params)) for o in cls.operations]
        if len(op_signatures) != len(set(op_signatures)):
            errors.append(f"Class '{cls.name}' memiliki operasi duplikat dengan signature sama.")
        for attr in cls.attributes:
            if not re.match(r"^[A-Za-z_]\w*$", attr.name):
                errors.append(f"Nama atribut '{attr.name}' di class '{cls.name}' tidak valid.")
            gt = go_type(attr.type_name)
            if not gt or not re.match(r"^(\[\]|\*)?([A-Za-z_]\w*)(\.[A-Za-z_]\w*)?$", gt):
                errors.append(f"Tipe atribut '{attr.name}: {attr.type_name}' tidak dapat dipetakan dengan aman ke Go.")
            if gt not in {"string","int","int64","bool","float64","float32","time.Time"} and not gt.startswith(("[]","*")):
                warnings.append(f"Tipe '{attr.type_name}' pada {cls.name}.{attr.name} dianggap tipe Go kustom; pastikan tipe itu didefinisikan.")
        for op in cls.operations:
            for p in op.params:
                if not re.match(r"^[A-Za-z_]\w*$", p.name):
                    errors.append(f"Nama parameter '{p.name}' pada operasi '{op.name}' tidak valid.")
            if op.return_type and not re.match(r"^(\[\]|\*)?([A-Za-z_]\w*)(\.[A-Za-z_]\w*)?$", go_type(op.return_type)):
                errors.append(f"Tipe return '{op.return_type}' pada operasi '{op.name}' tidak valid.")
        sm = cls.state_machine
        if sm:
            state_names = [s.name for s in sm.states]
            if not state_names:
                errors.append(f"State machine '{sm.name}' harus mendeklarasikan minimal satu state.")
            if len(state_names) != len(set(state_names)):
                errors.append(f"State machine '{sm.name}' memiliki state duplikat.")
            if sm.initial not in state_names:
                errors.append(f"Initial state '{sm.initial}' tidak ditemukan pada state machine '{sm.name}'.")
            for tr in sm.transitions:
                if tr.source not in state_names:
                    errors.append(f"State asal '{tr.source}' pada transition '{tr.event}' tidak ditemukan.")
                if tr.target not in state_names:
                    errors.append(f"State tujuan '{tr.target}' pada transition '{tr.event}' tidak ditemukan.")
    association_keys = set()
    for assoc in model.associations:
        if assoc.source not in class_map:
            errors.append(f"Association source class '{assoc.source}' tidak ditemukan.")
            continue
        if assoc.target not in class_map:
            errors.append(f"Association target class '{assoc.target}' tidak ditemukan.")
            continue
        if not re.match(r"^[A-Za-z_]\w*$", assoc.field_name):
            errors.append(f"Nama field association '{assoc.field_name}' tidak valid.")
        key = (assoc.source, assoc.field_name)
        if key in association_keys:
            errors.append(f"Association field '{assoc.field_name}' pada '{assoc.source}' didefinisikan lebih dari sekali.")
        association_keys.add(key)
        source_cls = class_map[assoc.source]
        if any(a.name == assoc.field_name for a in source_cls.attributes):
            errors.append(f"Association field '{assoc.field_name}' bertabrakan dengan atribut class '{assoc.source}'.")
        if assoc.multiplicity not in ("one", "optional", "many"):
            errors.append(f"Multiplicity '{assoc.multiplicity}' tidak didukung.")

    # Detect inheritance cycles with DFS.
    def visit(name, trail):
        if name in trail:
            errors.append("Siklus inheritance terdeteksi: " + " -> ".join(trail + [name]))
            return
        parent = class_map[name].parent
        if parent in class_map:
            visit(parent, trail + [name])
    for name in class_map: visit(name, [])
    if errors:
        raise SemanticError("\n".join(dict.fromkeys(errors)))
    return list(dict.fromkeys(warnings))
