import pytest
from redcode import Instruction, ADD, JMP, M_AB, M_A, IMMEDIATE, DIRECT, Point2D
from core import Core
from mars import MARS, Warrior

def test_position_calculation_with_add():
    """Test position calculations with repeated ADD operations in a 10x10 grid."""
    
    # Create a warrior with a single ADD instruction
    warrior = Warrior(name="test", author="test")
    warrior.instructions = {
        Point2D(0, 0): Instruction(opcode=ADD, modifier=M_AB, a_mode=IMMEDIATE, b_mode=IMMEDIATE, a_number=7, b_number=0),
        Point2D(1, 0): Instruction(opcode=JMP, modifier=M_A, a_mode=DIRECT, b_mode=DIRECT, a_number=-1, b_number=-1)
    }

    core = Core(width=10, size=100)
    mars = MARS(core=core, warriors = [warrior])
    
    # Expected positions after each ADD #7, 1 operation
    expected_positions = [
        Point2D(0, 0), 
        Point2D(7, 0),   # 0 + 7 = 7
        Point2D(4, 1),   # 7 + 7 = 14 -> wraps to (4,1)
        Point2D(1, 2),   # 4 + 7 = 11 -> wraps to (1,2)
        Point2D(8, 2),   # 1 + 7 = 8
        Point2D(5, 3),   # 8 + 7 = 15 -> wraps to (5,3)
        Point2D(2, 4),   # 5 + 7 = 12 -> wraps to (2,4)
        Point2D(9, 4),   # 2 + 7 = 9
        Point2D(6, 5),   # 9 + 7 = 16 -> wraps to (6,5)
        Point2D(3, 6),   # 6 + 7 = 13 -> wraps to (3,6)
        Point2D(0, 7),   # 3 + 7 = 10 -> wraps to (0,7)
        Point2D(7, 7),   # 0 + 7 = 7
        Point2D(4, 8),   # 7 + 7 = 14 -> wraps to (4,8)
        Point2D(1, 9),   # 4 + 7 = 11 -> wraps to (1,9)
        Point2D(8, 9),   # 1 + 7 = 8
        Point2D(5, 0),   # 8 + 7 = 15 -> wraps to (5,0)
        Point2D(2, 1),   # 5 + 7 = 12 -> wraps to (2,1)
        Point2D(9, 1),   # 2 + 7 = 9
        Point2D(6, 2),   # 9 + 7 = 16 -> wraps to (6,2)
        Point2D(3, 3),   # 6 + 7 = 13 -> wraps to (3,3)
        Point2D(0, 4),   # 3 + 7 = 10 -> wraps to (0,4)
    ]
    
    # Run 20 steps and verify positions
    for i in range(20):
        instruction = core[Point2D(0, 0)]
        expected_pos = expected_positions[i]
        calculated_address = (7*i) % 100
        assert calculated_address == mars.point_to_index(expected_pos), f"Step {i}: Expected address{expected_pos}, got {calculated_address}"
        
        # Verify the instruction at the current position
        assert instruction.opcode == ADD, f"Step {i}: Expected ADD instruction"
        assert instruction.b_number == 7*i, f"Step {i}: Expected b_number=0" 
        assert instruction.a_number == 7, f"Step {i}: Expected a_number=7"
        
        mars.step() # ADD
        mars.step() # JMP

def test_position_calculation_with_add_negative():
    """Test position calculations with repeated ADD operations in a 10x10 grid."""
    
    # Create a warrior with a single ADD instruction
    warrior = Warrior(name="test", author="test")
    warrior.instructions = {
        Point2D(0, 0): Instruction(opcode=ADD, modifier=M_AB, a_mode=IMMEDIATE, b_mode=IMMEDIATE, a_number=-7, b_number=0),
        Point2D(1, 0): Instruction(opcode=JMP, modifier=M_A, a_mode=DIRECT, b_mode=DIRECT, a_number=-1, b_number=-1)
    }

    core = Core(width=10, size=100)
    mars = MARS(core=core, warriors = [warrior])
    
    # Expected positions after each ADD #7, 1 operation
    expected_positions = [
        Point2D(0, 0), 
        Point2D(3, 9),
        Point2D(6, 8),
        Point2D(9, 7),
        Point2D(2, 7),
        Point2D(5, 6),
        Point2D(8, 5),
        Point2D(1, 5),
        Point2D(4, 4),
        Point2D(7, 3),
        Point2D(0, 3),
        Point2D(3, 2),
        Point2D(6, 1),
        Point2D(9, 0),
        Point2D(2, 0),
        Point2D(5, 9),
    ]
    
    # Run 20 steps and verify positions
    for i in range(16):
        instruction = core[Point2D(0, 0)]
        expected_pos = expected_positions[i]
        calculated_address = (-7*i) % 100
        assert calculated_address == mars.point_to_index(expected_pos), f"Step {i}: Expected address{expected_pos}, got {calculated_address}"
        
        # Verify the instruction at the current position
        assert instruction.opcode == ADD, f"Step {i}: Expected ADD instruction"
        assert instruction.b_number == -7*i, f"Step {i}: Expected b_number=0" 
        assert instruction.a_number == -7, f"Step {i}: Expected a_number=7"
        
        mars.step() # ADD
        mars.step() # JMP
