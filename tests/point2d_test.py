import unittest
from redcode import Point2D, Instruction, MOV, M_F, DIRECT

class TestPoint2D(unittest.TestCase):
    def test_backward_compatibility(self):
        # Test that numbers work the same as Point2D with y=0
        p = Point2D(42)
        self.assertEqual(p.x, 42)
        self.assertEqual(p.y, 0)
        self.assertEqual(str(p), "42")

    def test_2d_parsing(self):
        # Test parsing of 2D values
        p = Point2D(1, 2)
        self.assertEqual(p.x, 1)
        self.assertEqual(p.y, 2)
        self.assertEqual(str(p), "1;2")

    def test_instruction_parsing(self):
        # Test that instructions handle both numbers and 2D points
        instr1 = Instruction(MOV, M_F, DIRECT, "42", DIRECT, "0")
        self.assertEqual(str(instr1.a_number), "42")
        self.assertEqual(str(instr1.b_number), "0")

        instr2 = Instruction(MOV, M_F, DIRECT, "1;2", DIRECT, "3;4")
        self.assertEqual(str(instr2.a_number), "1;2")
        self.assertEqual(str(instr2.b_number), "3;4")

if __name__ == '__main__':
    unittest.main() 