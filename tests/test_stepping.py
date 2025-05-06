import pytest
from redcode import parse, Instruction, STEP_NORMAL, STEP_VERTICAL, STEP_BACKWARD, STEP_VERTICAL_BACKWARD, Point2D

def test_parse_stepping_modifiers():
    # Test default stepping (no modifier)
    warrior = parse(['MOV.I #0, 0'])
    assert warrior.instructions[0].stepping == STEP_NORMAL
    
    # Test W (vertical backward)
    warrior = parse(['MOV.I.W #0, 0:1'])
    assert warrior.instructions[0].stepping == STEP_VERTICAL_BACKWARD
    assert isinstance(warrior.instructions[0].b_number, Point2D)
    assert warrior.instructions[0].b_number.x == 0
    assert warrior.instructions[0].b_number.y == 1
    
    # Test A (backward)
    warrior = parse(['MOV.I.Q #0, 0'])
    assert warrior.instructions[0].stepping == STEP_BACKWARD
    
    # Test S (vertical)
    warrior = parse(['MOV.I.S #0, 0:1'])
    assert warrior.instructions[0].stepping == STEP_VERTICAL
    assert isinstance(warrior.instructions[0].b_number, Point2D)
    assert warrior.instructions[0].b_number.x == 0
    assert warrior.instructions[0].b_number.y == 1
    
    # Test D (normal)
    warrior = parse(['MOV.I.D #0, 0'])
    assert warrior.instructions[0].stepping == STEP_NORMAL

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
    
    assert isinstance(warrior.instructions[0].a_number, Point2D)
    assert warrior.instructions[0].a_number.x == 1
    assert warrior.instructions[0].a_number.y == 2
    assert isinstance(warrior.instructions[0].b_number, Point2D)
    assert warrior.instructions[0].b_number.x == 3
    assert warrior.instructions[0].b_number.y == 4

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
    
    assert warrior.instructions[0].stepping == STEP_VERTICAL_BACKWARD
    assert warrior.instructions[1].stepping == STEP_BACKWARD
    assert warrior.instructions[2].stepping == STEP_VERTICAL
    assert warrior.instructions[3].stepping == STEP_NORMAL

def test_stepping_with_labels():
    # Test stepping with labels
    warrior = parse([
        'start MOV.I.W #0, target',
        'target ADD.I.Q #1, start'
    ])
    
    assert warrior.instructions[0].stepping == STEP_VERTICAL_BACKWARD
    assert warrior.instructions[1].stepping == STEP_BACKWARD 
