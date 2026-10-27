"""Compiler facade: parse -> semantic validation -> generate."""
from dataclasses import dataclass
from .parser import parse, ParseError
from .semantic import validate, SemanticError
from .codegen import generate

@dataclass
class CompileResult:
    output: str
    class_count: int
    warnings: list[str]

class CompileError(Exception):
    pass

def compile_source(source: str, package_name: str = "main") -> CompileResult:
    try:
        model = parse(source)
        warnings = validate(model)
        output = generate(model, package_name)
        return CompileResult(output, len(model.classes), warnings)
    except (ParseError, SemanticError, ValueError, SyntaxError) as exc:
        raise CompileError(str(exc)) from exc
