import unittest
from xtuml_go.compiler import compile_source, CompileError

SAMPLE = """@startuml
class Student {
  +name: String
  -age: Integer
  +IsAdult(): Boolean
}
@enduml
"""

STATE_SAMPLE = """class Order {
  +id: String
}
state_machine OrderLifecycle for Order {
  initial Pending
  state Pending
  state Paid
  transition Pending on Pay -> Paid action MarkPaid
}
"""

class CompilerTests(unittest.TestCase):
    def test_class_generates_struct_and_constructor(self):
        result = compile_source(SAMPLE)
        self.assertIn("type Student struct", result.output)
        self.assertIn("func NewStudent", result.output)
        self.assertIn("Name string", result.output)
        self.assertIn("age int", result.output)

    def test_method_stub(self):
        result = compile_source(SAMPLE)
        self.assertIn("func (self *Student) IsAdult() bool", result.output)

    def test_state_machine_generates_handler(self):
        result = compile_source(STATE_SAMPLE)
        self.assertIn("HandleOrderLifecycleEvent", result.output)
        self.assertIn('"Pay"', result.output)

    def test_association_generates_collection_field(self):
        result = compile_source("""class Student {\n +name: String\n}\nclass Course {\n +title: String\n}\nassociation Student courses Course many\n""")
        self.assertIn("Courses []Course", result.output)
        self.assertIn("Courses: make([]Course, 0)", result.output)

    def test_state_machine_initial_state_is_initialized(self):
        result = compile_source(STATE_SAMPLE)
        self.assertIn("orderLifecycleState: OrderLifecyclePending", result.output)
        self.assertIn("self.orderLifecycleState = OrderLifecyclePaid", result.output)

    def test_unknown_parent_fails(self):
        with self.assertRaises(CompileError):
            compile_source("class Child extends Missing {\\n +name: String\\n}")

    def test_invalid_package_fails(self):
        with self.assertRaises(CompileError):
            compile_source(SAMPLE, "Main")

if __name__ == "__main__":
    unittest.main()
