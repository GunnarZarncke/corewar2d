from copy import copy
from random import randint, choices, seed
from redcode import (
    DAT, MOV, ADD, SUB, MUL, DIV, MOD, JMP, JMZ, JMN, DJN, SPL, SLT, CMP, SEQ, SNE, NOP,
    M_A, M_B, M_AB, M_BA, M_F, M_X, M_I,
    STEP_NORMAL, STEP_VERTICAL, STEP_BACKWARD, STEP_VERTICAL_BACKWARD,
    IMMEDIATE, DIRECT, INDIRECT_B, PREDEC_B, POSTINC_B, INDIRECT_A, PREDEC_A, POSTINC_A,
    Point2D
)

# Define mutation weights
MUTATION_WEIGHTS = {
    'opcode': 5,
    'modifier': 3,
    'stepping': 2,
    'a_mode': 3,
    'a_value': 10,
    'b_mode': 3,
    'b_value': 10
}

# Define possible values for each field
OPCODES = [DAT, MOV, ADD, SUB, MUL, DIV, MOD, JMP, JMZ, JMN, DJN, SPL, SLT, CMP, SEQ, SNE, NOP]
MODIFIERS = [M_A, M_B, M_AB, M_BA, M_F, M_X, M_I]
STEPPING_MODES = [STEP_NORMAL, STEP_VERTICAL, STEP_BACKWARD, STEP_VERTICAL_BACKWARD]
ADDRESSING_MODES = [IMMEDIATE, DIRECT, INDIRECT_B, PREDEC_B, POSTINC_B, INDIRECT_A, PREDEC_A, POSTINC_A]

OPCODE_WEIGHTS = {
    MOV: 0.05,
    ADD: 0.05 * (100 / 400),     
    SUB: 0.05 * (100 / 400),     
    MUL: 0.05 * (100 / 5000),    
    DIV: 0.05 * (100 / 5000),    
    MOD: 0.05 * (100 / 500),    
    JMP: 0.05 * (100 / 200),     
    JMZ: 0.05 * (100 / 250),     
    JMN: 0.05 * (100 / 250),     
    DJN: 0.05 * (100 / 500),     
    SPL: 0.05 * (100 / 2000),    
    SLT: 0.05 * (100 / 400),     
    CMP: 0.05 * (100 / 400),     
    SEQ: 0.05 * (100 / 400),     
    SNE: 0.05 * (100 / 400),     
    NOP: 0.05 * (100 / 25),      
}

OPCODE_WEIGHTS[DAT] = 1 - sum(OPCODE_WEIGHTS.values())
print(OPCODE_WEIGHTS)

ADDRESSING_MODE_WEIGHTS = {
    IMMEDIATE: 8, DIRECT: 4, INDIRECT_B: 2, PREDEC_B: 1, POSTINC_B: 1, INDIRECT_A: 2, PREDEC_A: 1, POSTINC_A: 1
}

def mutate_value(value):
    """Mutate a value by adding or subtracting a power of 2.
    
    Args:
        value: The current value (Point2D)
        
    Returns:
        The mutated value (Point2D)
    """
    # Select a power of 2 (1 to 16)
    power = randint(1, 16)
    change = 2 ** power
    
    # 50% chance to subtract instead of add
    if randint(0, 1) == 0:
        change = -change
    
    # 50% chance to change x or y
    if randint(0, 1) == 0:
        new_x = (value.x + change) 
        new_y = value.y
    else:
        new_x = value.x
        new_y = (value.y + change)
    
    return Point2D(new_x, new_y)

def mutate_instruction(instruction):
    """Mutate a single instruction by randomly changing one of its fields.
    
    Args:
        instruction: The instruction to mutate
        
    Returns:
        The mutated instruction
    """
    # Select which field to mutate based on weights
    mutation_type = choices(
        list(MUTATION_WEIGHTS.keys()),
        weights=list(MUTATION_WEIGHTS.values()),
        k=1
    )[0]
    
    # Create a copy of the instruction to mutate
    mutated = copy(instruction)
    
    # Apply the selected mutation
    if mutation_type == 'opcode':
        # Use weighted selection for opcodes
        mutated.opcode = choices(
            list(OPCODE_WEIGHTS.keys()),
            weights=list(OPCODE_WEIGHTS.values()),
            k=1
        )[0]
    elif mutation_type == 'modifier':
        mutated.modifier = choices(MODIFIERS, k=1)[0]
    elif mutation_type == 'stepping':
        mutated.stepping = choices(STEPPING_MODES, k=1)[0]
    elif mutation_type == 'a_mode':
        # Use weighted selection for addressing modes
        mutated.a_mode = choices(
            list(ADDRESSING_MODE_WEIGHTS.keys()),
            weights=list(ADDRESSING_MODE_WEIGHTS.values()),
            k=1
        )[0]
    elif mutation_type == 'a_value':
        mutated.a_number = mutate_value(mutated.a_number)
    elif mutation_type == 'b_mode':
        # Use weighted selection for addressing modes
        mutated.b_mode = choices(
            list(ADDRESSING_MODE_WEIGHTS.keys()),
            weights=list(ADDRESSING_MODE_WEIGHTS.values()),
            k=1
        )[0]
    elif mutation_type == 'b_value':
        mutated.b_number = mutate_value(mutated.b_number)
    
    return mutated

def mutate_core(mars, num_mutations=1, seed_value=None):
    """Mutate random instructions in the core.
    
    Args:
        mars: The MARS instance containing the core to mutate
        num_mutations: Number of mutations to perform
        seed_value: Optional seed for reproducible mutations
        
    Returns:
        The number of mutations performed
    """
    if seed_value is not None:
        seed(seed_value)
    
    mutations_performed = 0
    
    for _ in range(num_mutations):
        # Select a random position in the core
        x = randint(0, mars.core.width - 1)
        y = randint(0, mars.core.height - 1)
        pos = Point2D(x, y)
        
        # Get the instruction at that position
        instruction = mars.get_instruction(pos)
        
        # Mutate the instruction
        mutated = mutate_instruction(instruction)
        
        # Store the mutated instruction back in the core
        mars.set_instruction(pos, mutated)
        mutations_performed += 1
    
    return mutations_performed 