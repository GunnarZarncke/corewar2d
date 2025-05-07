import pytest
from redcode import parse, Instruction, STEP_NORMAL, STEP_VERTICAL, STEP_BACKWARD, STEP_VERTICAL_BACKWARD, Point2D, PREDEC_A, POSTINC_A, INDIRECT_A
from mars import MARS
from core import Core

def test_parse_stepping_modifiers():
    # Test default stepping (no modifier)
    warrior = parse(['MOV.I #0, 0'])
    assert warrior.instructions[Point2D(0, 0)].stepping == STEP_NORMAL
    
    # Test W (vertical backward)
    warrior = parse(['MOV.I.W #0, 0:1'])
    assert warrior.instructions[Point2D(0, 0)].stepping == STEP_VERTICAL_BACKWARD
    assert isinstance(warrior.instructions[Point2D(0, 0)].b_number, Point2D)
    assert warrior.instructions[Point2D(0, 0)].b_number.x == 0
    assert warrior.instructions[Point2D(0, 0)].b_number.y == 1
    
    # Test Q (backward)
    warrior = parse(['MOV.I.Q #0, 0'])
    assert warrior.instructions[Point2D(0, 0)].stepping == STEP_BACKWARD
    
    # Test S (vertical)
    warrior = parse(['MOV.I.S #0, 0:1'])
    assert warrior.instructions[Point2D(0, 0)].stepping == STEP_VERTICAL
    assert isinstance(warrior.instructions[Point2D(0, 0)].b_number, Point2D)
    assert warrior.instructions[Point2D(0, 0)].b_number.x == 0
    assert warrior.instructions[Point2D(0, 0)].b_number.y == 1
    
    # Test D (normal)
    warrior = parse(['MOV.I.D #0, 0'])
    assert warrior.instructions[Point2D(0, 0)].stepping == STEP_NORMAL

def test_instruction_string_representation():
    # Test default stepping (no modifier shown)
    instr = Instruction('MOV', 'I', None, '#', '0', '$', '0')
    assert str(instr) == "MOV.I    # 0, $ 0"
    
    # Test W modifier
    instr = Instruction('MOV', 'I', 'W', '#', '0', '$', '0:1')
    assert str(instr) == "MOV.I .W # 0, $ 0:1"
    
    # Test A modifier
    instr = Instruction('MOV', 'I', 'Q', '#', '0', '$', '0')
    assert str(instr) == "MOV.I .Q # 0, $ 0"
    
    # Test S modifier
    instr = Instruction('MOV', 'I', 'S', '#', '0', '$', '0:1')
    assert str(instr) == "MOV.I .S # 0, $ 0:1"
    
    # Test D modifier (should not show in string representation)
    instr = Instruction('MOV', 'I', 'D', '#', '0', '$', '0')
    assert str(instr) == "MOV.I    # 0, $ 0"

def test_point2d_arithmetic():
    # Test Point2D arithmetic in instructions
    warrior = parse([
        'MOV.I.W #1:2, 3:4',
        'ADD.I.Q #1:1, 2:2'
    ])
    
    assert isinstance(warrior.instructions[Point2D(0, 0)].a_number, Point2D)
    assert warrior.instructions[Point2D(0, 0)].a_number.x == 1
    assert warrior.instructions[Point2D(0, 0)].a_number.y == 2
    assert isinstance(warrior.instructions[Point2D(0, 0)].b_number, Point2D)
    assert warrior.instructions[Point2D(0, 0)].b_number.x == 3
    assert warrior.instructions[Point2D(0, 0)].b_number.y == 4

def test_invalid_stepping_modifier():
    # Test invalid stepping modifier
    with pytest.raises(SyntaxError):
        parse(['MOV.I.X #0, 0'])  # X is not a valid stepping modifier

def test_stepping_with_different_instructions():
    # Test stepping with different instruction types
    warrior = parse([
        'MOV.I.W #0, 0:1',
        'ADD.I.Q #1, 1',
        'SUB.I.S #2, 2:1',
        'MUL.I.D #3, 3'
    ])
    
    assert warrior.instructions[Point2D(0, 0)].stepping == STEP_VERTICAL_BACKWARD
    assert warrior.instructions[Point2D(0, -1)].stepping == STEP_BACKWARD
    assert warrior.instructions[Point2D(-1, -1)].stepping == STEP_VERTICAL
    assert warrior.instructions[Point2D(-1, 0)].stepping == STEP_NORMAL

def test_stepping_with_labels():
    # Test stepping with labels
    warrior = parse([
        'start MOV.I.W #0, target',
        'target ADD.I.Q #1, start'
    ])
    
    assert warrior.instructions[Point2D(0, 0)].stepping == STEP_VERTICAL_BACKWARD
    assert warrior.instructions[Point2D(0, -1)].stepping == STEP_BACKWARD
    assert warrior.labels['target'] == Point2D(0, -1)
    assert warrior.labels['start'] == Point2D(0, 0)

def test_stepping_execution():
    """Test that stepping modes correctly update the PC during execution."""
    # Create a simple warrior with different stepping modes
    warrior = parse([
        'MOV.I.D #0, 0',      # Normal stepping
        'MOV.I.S #0, 0',      # Vertical stepping
        'MOV.I.Q #0, 0',      # Backward stepping
        'MOV.I.W #0, 0',      # Vertical backward stepping
    ])
    
    # Create a MARS instance with the warrior
    mars = MARS(warriors=[warrior], randomize=False)
    
    # Execute first instruction (D - normal stepping)
    mars.step()
    assert len(warrior.task_queue) == 1
    assert warrior.task_queue[0] == Point2D(1, 0)  # PC+1
    
    # Execute second instruction (S - vertical stepping)
    mars.step()
    assert len(warrior.task_queue) == 1
    assert warrior.task_queue[0] == Point2D(1, 1)  # PC+(0:1)
    
    # Execute third instruction (Q - backward stepping)
    mars.step()
    assert len(warrior.task_queue) == 1
    assert warrior.task_queue[0] == Point2D(0, 1)  # PC-1
    
    # Execute fourth instruction (W - vertical backward stepping)
    mars.step()
    assert len(warrior.task_queue) == 1
    assert warrior.task_queue[0] == Point2D(0, 0)  # PC-(0:1)

def test_stepping_with_jumps():
    """Test stepping modes with jump instructions."""
    warrior = parse([
        'JMP.D 1',           # Normal stepping jump
        'JMP.S 0:1',         # Vertical stepping jump
        'JMP.Q -1',          # Backward stepping jump
        'JMP.W 0:-1',        # Vertical backward stepping jump
    ])
    
    mars = MARS(warriors=[warrior], randomize=False)
    
    # Execute first instruction (D - normal stepping)
    mars.step()
    assert len(warrior.task_queue) == 1
    assert warrior.task_queue[0] == Point2D(1, 0)  # Jump to PC+1
    
    # Execute second instruction (S - vertical stepping)
    mars.step()
    assert len(warrior.task_queue) == 1
    assert warrior.task_queue[0] == Point2D(1, 1)  # Jump to PC+(0:1)
    
    # Execute third instruction (Q - backward stepping)
    mars.step()
    assert len(warrior.task_queue) == 1
    assert warrior.task_queue[0] == Point2D(0, 1)  # Jump to PC-1
    
    # Execute fourth instruction (W - vertical backward stepping)
    mars.step()
    assert len(warrior.task_queue) == 1
    assert warrior.task_queue[0] == Point2D(0, 0)  # Jump to PC-(0:1)

def test_stepping_with_conditional_jumps():
    """Test stepping modes with conditional jump instructions."""
    warrior = parse([
        'JMZ.D #0, 1',       # Normal stepping conditional jump
        'JMZ.S #0, 0:1',     # Vertical stepping conditional jump
        'JMZ.Q #0, -1',      # Backward stepping conditional jump
        'JMZ.W #0, 0:-1',    # Vertical backward stepping conditional jump
    ])
    
    mars = MARS(warriors=[warrior], randomize=False)
    
    # Execute first instruction (D - normal stepping)
    mars.step()
    assert len(warrior.task_queue) == 1
    assert warrior.task_queue[0] == Point2D(1, 0)  # Jump to PC+1
    
    # Execute second instruction (S - vertical stepping)
    mars.step()
    assert len(warrior.task_queue) == 1
    assert warrior.task_queue[0] == Point2D(1, 1)  # Jump to PC+(0:1)
    
    # Execute third instruction (Q - backward stepping)
    mars.step()
    assert len(warrior.task_queue) == 1
    assert warrior.task_queue[0] == Point2D(0, 1)  # Jump to PC-1
    
    # Execute fourth instruction (W - vertical backward stepping)
    mars.step()
    assert len(warrior.task_queue) == 1
    assert warrior.task_queue[0] == Point2D(0, 0)  # Jump to PC-(0:1)


def test_instruction_overlap_detection():
    """Test that overlapping instructions are detected."""
    with pytest.raises(ValueError, match="instruction position.*already used"):
        parse([
            'MOV.I.D #0, 0',      # (0,0)
            'MOV.I.Q #0, 0',      # (1,0)
            'MOV.I.D #0, 0',      # (0,0) - overlaps with first instruction
        ])


def test_2d_warrior_size():
    """Test that warrior size is correctly calculated in 2D space."""
    # Test a simple linear warrior
    warrior = parse([
        'MOV.I.D #0, 0',  # (0,0)
        'MOV.I.D #0, 0',  # (1,0)
        'MOV.I.D #0, 0',  # (2,0)
    ])
    assert warrior.get_size() == Point2D(3, 1)
    
    # Test a 2D warrior
    warrior = parse([
        'MOV.I.D #0, 0',  # (0,0)
        'MOV.I.S #0, 0',  # (0,1)
        'MOV.I.Q #0, 0',  # (-1,1)
        'MOV.I.W #0, 0',  # (-1,0)
    ])
    assert warrior.get_size() == Point2D(2, 2)
    
    # Test a sparse warrior
    warrior = parse([
        'MOV.I.D #0, 0',      # (0,0)
        'MOV.I.S #0, 0',      # (0,1)
        'MOV.I.S #0, 0',      # (0,2)
        'MOV.I.Q #0, 0',      # (-1,2)
        'MOV.I.Q #0, 0',      # (-2,2)
        'MOV.I.W #0, 0',      # (-2,1)
        'MOV.I.W #0, 0',      # (-2,0)
    ])
    assert warrior.get_size() == Point2D(3, 3)

def test_2d_instruction_iteration():
    """Test that iterating over warrior instructions works correctly."""
    warrior = parse([
        'MOV.I.D #0, 0',  # (0,0)
        'MOV.I.S #0, 0',  # (0,1)
        'MOV.I.Q #0, 0',  # (-1,1)
        'MOV.I.W #0, 0',  # (-1,0)
    ])
    
    # Test iteration
    instructions = list(warrior)
    assert len(instructions) == 4
    
    # Test that all instructions are present
    positions = set(warrior.instructions.keys())
    assert positions == {Point2D(0, 0), Point2D(1, 0), Point2D(1, 1), Point2D(0, 1)}
    
    # Test that each position has an instruction
    for pos in positions:
        assert pos in warrior.instructions
        assert isinstance(warrior.instructions[pos], Instruction) 

def test_stepping_increment_decrement():
    """Test that increment and decrement operations respect stepping modes."""
    
    def create_test_warrior():
        """Create a warrior with test and target instructions."""
        return parse([
            'NOP',
            'MOV.AB.D {2, -1',  # our test instruction modifies 
            'DAT',
            'DAT',
        ])
    
    def test_prepost_decrement(stepping_mode, mode, expected_value):
        """Test pre-decrement operation with given stepping mode."""
        # Create fresh warrior and MARS instance
        warrior = create_test_warrior()
        mars = MARS(warriors=[warrior], randomize=False)
        mars.step()   # over NOP
        
        # Get our test and target instructions
        test_instr = mars.core[Point2D(1)]
        target_instr = mars.core[Point2D(3)]
        
        # Set up the test
        test_instr.stepping = stepping_mode
        test_instr.a_mode = mode
        
        # Execute and verify
        mars.step()
        assert target_instr.a_number == expected_value
    
    # Test pre-decrement with all stepping modes
    test_prepost_decrement(STEP_NORMAL, PREDEC_A, Point2D(-1, 0))
    test_prepost_decrement(STEP_VERTICAL, PREDEC_A, Point2D(0, -1))
    test_prepost_decrement(STEP_BACKWARD, PREDEC_A, Point2D(1, 0))
    test_prepost_decrement(STEP_VERTICAL_BACKWARD, PREDEC_A, Point2D(0, 1))
    
    # Test post-increment with all stepping modes
    test_prepost_decrement(STEP_NORMAL, POSTINC_A, Point2D(1, 0))
    test_prepost_decrement(STEP_VERTICAL, POSTINC_A, Point2D(0, 1))
    test_prepost_decrement(STEP_BACKWARD, POSTINC_A, Point2D(-1, 0))
    test_prepost_decrement(STEP_VERTICAL_BACKWARD, POSTINC_A, Point2D(0, -1))
