import pytest
from redcode import (
    Instruction, ADD, SUB, MUL, DIV, MOD, JMP, JMZ, JMN, DJN, SPL,
    M_F, M_A, M_B, M_AB, M_BA, M_X, M_I,
    IMMEDIATE, DIRECT, INDIRECT_A, INDIRECT_B, PREDEC_A, PREDEC_B, POSTINC_A, POSTINC_B
)
from core import Core
from mars import MARS
from redcode import Warrior
from redcode import Point2D

def test_long_term_add_effects():
    """Test long-term effects of repeated ADD operations with different offsets."""
    # Test different ADD offsets that will cause interesting wrapping patterns
    test_cases = [
        (3, 1),  # Small offset, frequent wrapping
        (7, 1),  # Large offset, less frequent wrapping
        (9, 1),  # Almost full width, minimal movement
        (11, 1), # Larger than width, interesting wrapping
    ]
    
    for a_number, b_number in test_cases:
        warrior = Warrior(name=f"add_{a_number}_{b_number}", author="test")
        warrior.instructions = {
            Point2D(0, 0): Instruction(opcode=ADD, modifier=M_F, a_mode=IMMEDIATE, b_mode=DIRECT, 
                       a_number=a_number, b_number=b_number),
            Point2D(1, 0): Instruction(opcode=JMP, modifier=M_A, a_mode=DIRECT, b_mode=DIRECT, a_number=-1, b_number=-1)
        }
        
        core = Core(width=10, size=100)
        mars = MARS(core=core, warriors=[warrior])
        
        # Initialize at (0,0)
        current_pos = Point2D(0, 0)
        mars.enqueue(warrior, current_pos)
        
        # Run for multiple cycles to observe patterns
        positions = []
        for _ in range(100):  # Run for 100 steps
            mars.step()
            if warrior.task_queue:
                positions.append(warrior.task_queue[0])
        
        # Verify that we eventually return to a previous position (cycle detection)
        assert len(positions) > 0, "No positions recorded"
        assert positions[-1] in positions[:-1], "No cycle detected in ADD pattern"

def test_multiplicative_effects():
    """Test effects of multiplication operations on position calculations."""
    # Test different multiplication factors
    test_cases = [
        (2, 1),  # Doubling
        (3, 1),  # Tripling
        (5, 1),  # Larger prime factor
        (7, 1),  # Another prime factor
    ]
    
    for a_number, b_number in test_cases:
        warrior = Warrior(name=f"mul_{a_number}_{b_number}", author="test")
        warrior.instructions = {
            Point2D(0, 0): Instruction(opcode=MUL, modifier=M_F, a_mode=IMMEDIATE, b_mode=DIRECT,
                       a_number=a_number, b_number=b_number),
            Point2D(1, 0): Instruction(opcode=JMP, modifier=M_A, a_mode=DIRECT, b_mode=DIRECT, a_number=-1, b_number=-1)
        }
        
        core = Core(width=10, size=100)
        mars = MARS(core=core, warriors=[warrior])
        
        # Initialize at (1,0) to avoid multiplication by zero
        current_pos = Point2D(1, 0)
        mars.enqueue(warrior, current_pos)
        
        # Run for multiple cycles
        positions = []
        for _ in range(50):  # Run for 50 steps
            mars.step()
            if warrior.task_queue:
                positions.append(warrior.task_queue[0])
        
        print(positions)

        # Verify that multiplication leads to expected growth patterns
        assert len(positions) > 0, "No positions recorded"
        # Check that we eventually wrap around
        assert any(p.x != positions[0].x for p in positions), "No wrapping detected in MUL pattern"

def test_modulo_effects():
    """Test effects of modulo operations on position calculations."""
    # Test different modulo divisors
    test_cases = [
        (3, 1),  # Small divisor
        (5, 1),  # Medium divisor
        (7, 1),  # Larger divisor
        (9, 1),  # Almost full width
    ]
    
    for a_number, b_number in test_cases:
        warrior = Warrior(name=f"mod_{a_number}_{b_number}", author="test")
        warrior.instructions = {
            Point2D(0, 0): Instruction(opcode=MOD, modifier=M_F, a_mode=IMMEDIATE, b_mode=DIRECT,
                       a_number=a_number, b_number=b_number),
            Point2D(1, 0): Instruction(opcode=JMP, modifier=M_A, a_mode=DIRECT, b_mode=DIRECT, a_number=-1, b_number=-1)
        }
        
        core = Core(width=10, size=100)
        mars = MARS(core=core, warriors=[warrior])
        
        # Initialize at (1,0)
        current_pos = Point2D(1, 0)
        mars.enqueue(warrior, current_pos)
        
        # Run for multiple cycles
        positions = []
        for _ in range(50):
            mars.step()
            if warrior.task_queue:
                positions.append(warrior.task_queue[0])
        
        # Verify that modulo operations create repeating patterns
        assert len(positions) > 0, "No positions recorded"
        # Check for cycle in the pattern
        assert positions[-1] in positions[:-1], "No cycle detected in MOD pattern"

def test_combined_operations():
    """Test effects of combining different operations."""
    warrior = Warrior(name="combined_ops", author="test")
    warrior.instructions = {
        Point2D(0, 0): Instruction(opcode=ADD, modifier=M_F, a_mode=IMMEDIATE, b_mode=DIRECT, a_number=3, b_number=1),
        Point2D(1, 0): Instruction(opcode=MUL, modifier=M_F, a_mode=IMMEDIATE, b_mode=DIRECT, a_number=2, b_number=1),
        Point2D(2, 0): Instruction(opcode=MOD, modifier=M_F, a_mode=IMMEDIATE, b_mode=DIRECT, a_number=5, b_number=1),
        Point2D(3, 0): Instruction(opcode=JMP, modifier=M_A, a_mode=DIRECT, b_mode=DIRECT, a_number=-3, b_number=-3)
    }
    
    core = Core(width=10, size=100)
    mars = MARS(core=core, warriors=[warrior])
    
    # Initialize at (1,0)
    current_pos = Point2D(1, 0)
    mars.enqueue(warrior, current_pos)
    
    # Run for multiple cycles
    positions = []
    for _ in range(100):
        mars.step()
        if warrior.task_queue:
            positions.append(warrior.task_queue[0])
    
    # Verify that combined operations create complex but repeating patterns
    assert len(positions) > 0, "No positions recorded"
    # Check for cycle in the pattern
    assert positions[-1] in positions[:-1], "No cycle detected in combined operations pattern"

def test_addressing_mode_effects():
    """Test effects of different addressing modes on position calculations."""
    # Test different addressing mode combinations
    test_cases = [
        (IMMEDIATE, DIRECT),        # Basic immediate to direct
        (DIRECT, INDIRECT_A),       # Direct to indirect A
        (INDIRECT_A, PREDEC_A),     # Indirect A to pre-decrement A
        (PREDEC_A, POSTINC_A),      # Pre-decrement A to post-increment A
    ]
    
    for a_mode, b_mode in test_cases:
        warrior = Warrior(name=f"addr_{a_mode}_{b_mode}", author="test")
        warrior.instructions = {
            Point2D(0, 0): Instruction(opcode=ADD, modifier=M_F, a_mode=a_mode, b_mode=b_mode,
                       a_number=3, b_number=1),
            Point2D(1, 0): Instruction(opcode=JMP, modifier=M_A, a_mode=DIRECT, b_mode=DIRECT, a_number=-1, b_number=-1)
        }
        
        core = Core(width=10, size=100)
        mars = MARS(core=core, warriors=[warrior])
        
        # Initialize at (1,0)
        current_pos = Point2D(1, 0)
        mars.enqueue(warrior, current_pos)
        
        # Run for multiple cycles
        positions = []
        for _ in range(50):
            mars.step()
            if warrior.task_queue:
                positions.append(warrior.task_queue[0])
        
        # Verify that addressing modes affect position calculations
        assert len(positions) > 0, "No positions recorded"
        # Check that different addressing modes produce different patterns
        if a_mode != IMMEDIATE or b_mode != DIRECT:
            assert positions[1] != Point2D(4, 0), "Addressing modes not affecting position calculation" 
