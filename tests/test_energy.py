import pytest
from corewar.mars import MARS
from corewar.redcode import parse, Point2D, JMP

def test_energy_consumption():
    # Create a simple warrior with JMP 0 and explicit energy
    warrior_code = """
    ;name Test Energy
    ;author Test
    jmp 0 ; E:10
    """
    
    # Parse the warrior
    warrior = parse(warrior_code.split('\n'))
    
    # Create MARS with energy mode enabled
    mars = MARS(warriors=[warrior], total_energy=10)
    
    # Get initial position
    initial_pos = warrior.task_queue[0]
    initial_instruction = mars[initial_pos]
    
    # Verify initial energy
    assert initial_instruction.energy == 10, "Initial energy should be 10"
    
    # Run for 10 steps - exactly use up enegery
    for i in range(10):
        mars.step()
    
        assert len(warrior.task_queue) > 0, "Warrior should still be alive"
    
    # Get final instruction
    final_instruction = mars[initial_pos]
    
    # Verify energy is depleted
    assert final_instruction.energy == 0, "Energy should be depleted"
    
    # Verify warrior is still alive (task queue not empty)
    
    # Run one more step
    mars.step()
    
    # Verify instruction is not executed (energy is 0)
    assert final_instruction.energy == 0, "Energy should remain at 0"
    
    # Verify warrior is still alive (task queue not empty)
    assert len(warrior.task_queue) == 0, "Warrior should have died"

def test_instruction_energy_syntax():
    # Create a warrior with different energy values per instruction
    warrior_code = """
    ;name Test Energy Syntax
    ;author Test
    jmp 0 ; E:100
    mov 0, 1 ; E:50
    add #1, 2 ; E:200
    """
    
    # Parse the warrior
    warrior = parse(warrior_code.split('\n'))
    
    # Create MARS with energy mode enabled
    mars = MARS(total_energy=1000)
    mars.warriors = [warrior]
    mars.load_warriors()
    
    # Get instructions
    instructions = list(warrior.instructions.values())
    
    # Verify energy values were set correctly
    assert instructions[0].energy == 100, "First instruction should have 100 energy"
    assert instructions[1].energy == 50, "Second instruction should have 50 energy"
    assert instructions[2].energy == 200, "Third instruction should have 200 energy"
    
    # Verify other instructions have default energy
    for instruction in instructions[3:]:
        assert instruction.energy == 1000, "Other instructions should have default energy"

def test_complex_instruction_energy():
    # Test complex instructions with energy values
    warrior_code = """
    ;name Test Complex Energy
    ;author Test
    mov #1, @2 ; E:100
    add.b $3, *4 ; E:50
    jmp <5 ; E:200
    """
    
    # Parse the warrior
    warrior = parse(warrior_code.split('\n'))
    
    # Create MARS with energy mode enabled
    mars = MARS(total_energy=1000)
    mars.warriors = [warrior]
    mars.load_warriors()
    
    # Get instructions
    instructions = list(warrior.instructions.values())
    
    # Verify energy values were set correctly
    assert instructions[0].energy == 100, "First instruction should have 100 energy"
    assert instructions[1].energy == 50, "Second instruction should have 50 energy"
    assert instructions[2].energy == 200, "Third instruction should have 200 energy"
    
    # Verify instruction fields were parsed correctly
    assert str(instructions[0]) == "MOV.AB   # 1, @ 2; E:100", "First instruction parsing failed"
    assert str(instructions[1]) == "ADD.B    $ 3, * 4; E:50", "Second instruction parsing failed"
    assert str(instructions[2]) == "JMP.B    < 5, $ 0; E:200", "Third instruction parsing failed"

def test_energy_with_regular_comments():
    # Test energy values with regular comments
    warrior_code = """
    ;name Test Energy Comments
    ;author Test
    jmp 0 ; E:100 ; This is a regular comment
    mov 0, 1 ; E:50 ; Another comment
    add #1, 2 ; E:200 ; Final comment
    """
    
    # Parse the warrior
    warrior = parse(warrior_code.split('\n'))
    
    # Create MARS with energy mode enabled
    mars = MARS(total_energy=1000)
    mars.warriors = [warrior]
    mars.load_warriors()
    
    # Get instructions
    instructions = list(warrior.instructions.values())
    
    # Verify energy values were set correctly
    assert instructions[0].energy == 100, "First instruction should have 100 energy"
    assert instructions[1].energy == 50, "Second instruction should have 50 energy"
    assert instructions[2].energy == 200, "Third instruction should have 200 energy"

def test_single_argument_energy():
    # Test energy values with single argument instructions
    warrior_code = """
    ;name Test Single Arg Energy
    ;author Test
    jmp 0 ; E:100
    spl 1 ; E:50
    nop ; E:200
    """
    
    # Parse the warrior
    warrior = parse(warrior_code.split('\n'))
    
    # Create MARS with energy mode enabled
    mars = MARS(total_energy=1000)
    mars.warriors = [warrior]
    mars.load_warriors()
    
    # Get instructions
    instructions = list(warrior.instructions.values())
    
    # Verify energy values were set correctly
    assert instructions[0].energy == 100, "First instruction should have 100 energy"
    assert instructions[1].energy == 50, "Second instruction should have 50 energy"
    assert instructions[2].energy == 200, "Third instruction should have 200 energy" 