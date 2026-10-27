"""Intermediate representation (IR) for the supported xtUML subset."""
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Attribute:
    name: str
    type_name: str
    visibility: str = "+"
    default: Optional[str] = None

@dataclass
class Parameter:
    name: str
    type_name: str

@dataclass
class Operation:
    name: str
    params: list[Parameter] = field(default_factory=list)
    return_type: Optional[str] = None
    visibility: str = "+"

@dataclass
class State:
    name: str

@dataclass
class Transition:
    source: str
    event: str
    target: str
    action: Optional[str] = None

@dataclass
class StateMachine:
    name: str
    initial: str
    states: list[State] = field(default_factory=list)
    transitions: list[Transition] = field(default_factory=list)

@dataclass
class Association:
    source: str
    field_name: str
    target: str
    multiplicity: str = "one"  # one, optional, many

@dataclass
class UMLClass:
    name: str
    attributes: list[Attribute] = field(default_factory=list)
    operations: list[Operation] = field(default_factory=list)
    parent: Optional[str] = None
    state_machine: Optional[StateMachine] = None

@dataclass
class Model:
    classes: list[UMLClass] = field(default_factory=list)
    associations: list[Association] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
