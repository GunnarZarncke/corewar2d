import pytest
from copy import copy
from redcode import Instruction, Point2D
from mutator import mutate_instruction, mutate_core, MUTATION_WEIGHTS
from mars import MARS
from core import Core, DEFAULT_INITIAL_INSTRUCTION

def test_mutate_instruction():
    # Create a test instruction
    original = copy(DEFAULT_INITIAL_INSTRUCTION)
    
    # Test that mutation creates a new instruction
    mutated, was_changed = mutate_instruction(original)
    assert mutated is not original
    assert isinstance(mutated, Instruction)
    
    if was_changed:
        # Test that at least one field is different
        assert (mutated.opcode != original.opcode or
                mutated.modifier != original.modifier or
                mutated.stepping != original.stepping or
                mutated.a_mode != original.a_mode or
                mutated.a_number != original.a_number or
                mutated.b_mode != original.b_mode or
                mutated.b_number != original.b_number), f"Mutated: {mutated}, Original: {original}"
    
        assert isinstance(mutated.a_number, Point2D)
        assert isinstance(mutated.b_number, Point2D)

def test_mutate_core():
    # Create a test MARS instance with a small core
    core = Core(width=10, size=10)
    mars = MARS(core=core)
    
    # Fill core with known instructions
    for x in range(10):
        for y in range(10):
            pos = Point2D(x, y)
            mars.set_instruction(pos, copy(DEFAULT_INITIAL_INSTRUCTION))
    
    # Perform mutations
    num_mutations = 5
    mutations_performed = mutate_core(mars, num_mutations)
    
    # Verify number of mutations
    assert mutations_performed == num_mutations
    
    # Verify that some instructions were changed
    changed = 0
    for x in range(10):
        for y in range(10):
            pos = Point2D(x, y)
            instr = mars.get_instruction(pos)
            if instr.opcode != 1 or instr.modifier != 6:  # MOV.I
                changed += 1
    
    assert changed > 0

def test_mutation_weights():
    # Test that weights are properly defined
    assert 'opcode' in MUTATION_WEIGHTS
    assert 'modifier' in MUTATION_WEIGHTS
    assert 'stepping' in MUTATION_WEIGHTS
    assert 'a_mode' in MUTATION_WEIGHTS
    assert 'a_value' in MUTATION_WEIGHTS
    assert 'b_mode' in MUTATION_WEIGHTS
    assert 'b_value' in MUTATION_WEIGHTS
    
    # Test that weights match requirements
    assert MUTATION_WEIGHTS['opcode'] == 5
    assert MUTATION_WEIGHTS['modifier'] == 3
    assert MUTATION_WEIGHTS['stepping'] == 2
    assert MUTATION_WEIGHTS['a_mode'] == 3
    assert MUTATION_WEIGHTS['a_value'] == 10
    assert MUTATION_WEIGHTS['b_mode'] == 3
    assert MUTATION_WEIGHTS['b_value'] == 10 