#! /usr/bin/env python3
# coding: utf-8

from copy import copy
import re

__all__ = ['parse', 'DAT', 'MOV', 'ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'JMP',
           'JMZ', 'JMN', 'DJN', 'SPL', 'SLT', 'CMP', 'SEQ', 'SNE', 'NOP',
           'M_A', 'M_B', 'M_AB', 'M_BA', 'M_F', 'M_X', 'M_I', 'IMMEDIATE',
           'DIRECT', 'INDIRECT_B', 'PREDEC_B', 'POSTINC_B', 'INDIRECT_A',
           'PREDEC_A', 'POSTINC_A', 'Instruction', 'Warrior']

DAT = 0     # terminate process
MOV = 1     # move from A to B
ADD = 2     # add A to B, store result in B
SUB = 3     # subtract A from B, store result in B
MUL = 4     # multiply A by B, store result in B
DIV = 5     # divide B by A, store result in B if A <> 0, else terminate
MOD = 6     # divide B by A, store remainder in B if A <> 0, else terminate
JMP = 7     # transfer execution to A
JMZ = 8     # transfer execution to A if B is zero
JMN = 9     # transfer execution to A if B is non-zero
DJN = 10    # decrement B, if B is non-zero, transfer execution to A
SPL = 11    # split off process to A
SLT = 12    # skip next instruction if A is less than B
CMP = 13    # same as SEQ
SEQ = 14    # Skip next instruction if A is equal to B
SNE = 15    # Skip next instruction if A is not equal to B
NOP = 16    # No operation

# Instructions read and write A-fields.
M_A = 0

# Instructions read and write B-fields.
M_B = 1

# Instructions read the A-field of the A-instruction and the B-field of the
# B-instruction and write to B-fields.
M_AB = 2

# Instructions read the B-field of the A-instruction and the A-field of the
# B-instruction and write to A-fields.
M_BA = 3

# Instructions read both A- and B-fields of the A and B-instruction and
# write to both A- and B-fields (A to A and B to B).
M_F = 4

# Instructions read both A- and B-fields of the A and B-instruction  and
# write  to both A- and B-fields exchanging fields (A to B and B to A).
M_X = 5

# Instructions read and write entire instructions.
M_I = 6

# Stepping modifiers
STEP_NORMAL = 0  # PC+1 (default)
STEP_VERTICAL = 1  # PC+(0:1)
STEP_BACKWARD = 2  # PC-1
STEP_VERTICAL_BACKWARD = 3  # PC-(0:1)

STEP_MODIFIERS = {
    'D': STEP_NORMAL,
    'S': STEP_VERTICAL,
    'Q': STEP_BACKWARD,
    'W': STEP_VERTICAL_BACKWARD
}

IMMEDIATE = 0   # immediate
DIRECT = 1      # direct
INDIRECT_B = 2  # indirect using B-field
PREDEC_B  = 3   # predecrement indirect using B-field
POSTINC_B = 4   # postincrement indirect using B-field
INDIRECT_A = 5  # indirect using A-field
PREDEC_A = 6    # predecrement indirect using A-field
POSTINC_A = 7   # postincrement indirect using A-field

MODES = { '#': IMMEDIATE, '$': DIRECT, '@': INDIRECT_B, '<': PREDEC_B,
          '>': POSTINC_B, '*': INDIRECT_A, '{': PREDEC_A, '}': POSTINC_A }

INSTRUCTION_REGEX = re.compile(r'([a-z]{3})'  # opcode
                               r'(?:\s*\.\s*([abfxi]{1,2}))?' # optional modifier
                               r'(?:\s*\.\s*([wqsd]))?' # optional stepping modifier
                               r'(?:\s*([#\$\*@\{<\}>])?\s*([^,$]+))?' # optional first value
                               r'(?:\s*,\s*([#\$\*@\{<\}>])?\s*([^,]+))?$', # optional second value
                               re.I)

OPCODES = {'DAT': DAT, 'MOV': MOV, 'ADD': ADD, 'SUB': SUB, 'MUL': MUL,
           'DIV': DIV, 'MOD': MOD, 'JMP': JMP, 'JMZ': JMZ, 'JMN': JMN,
           'DJN': DJN, 'SPL': SPL, 'SLT': SLT, 'CMP': CMP, 'SEQ': SEQ,
           'SNE': SNE, 'NOP': NOP}

MODIFIERS = {'A': M_A, 'B': M_B, 'AB': M_AB, 'BA': M_BA, 'F': M_F, 'X': M_X,
             'I': M_I}

# ICWS'88 to ICWS'94 Conversion
# The default modifier for ICWS'88 emulation is determined according to the
# table below.
#        Opcode                             A-mode    B-mode    modifier
DEFAULT_MODIFIERS = {
        ('DAT', 'NOP')                 : {('#$@<>', '#$@<>'): 'F'},
        ('MOV','CMP')                  : {('#'    , '#$@<>'): 'AB',
                                          ('$@<>' , '#'    ): 'B' ,
                                          ('$@<>' , '$@<>' ): 'I'},
        ('ADD','SUB','MUL','DIV','MOD'): {('#'    , '#$@<>'): 'AB',
                                          ('$@<>' , '#'    ): 'B' ,
                                          ('$@<>' , '$@<>' ): 'F'},
        ('SLT', 'SEQ', 'SNE')          : {('#'    , '#$@<>'): 'AB',
                                          ('$@<>' , '#$@<>'): 'B'},
        ('JMP','JMZ','JMN','DJN','SPL'): {('#$@<>', '#$@<>'): 'B'}
    }

# Transform the readable form above, into the internal representation
DEFAULT_MODIFIERS = dict((tuple(OPCODES[opcode] for opcode in opcodes),
                         dict(((tuple(MODES[a] for a in ab_modes[0]),
                                tuple(MODES[b] for b in ab_modes[1])),
                               MODIFIERS[modifier]) for ab_modes, modifier in ab_modes_modifiers.items()))
                         for opcodes, ab_modes_modifiers in DEFAULT_MODIFIERS.items())

class Point2D:
    def __init__(self, x, y=0):
        if isinstance(x, str):
            if ':' in x:
                if y:
                    raise ValueError("Cannot provide both a string and a y value")
                x, y = map(int, x.split(':'))
            else:
                x = int(x)
                y = int(y)

            self.x = x
            self.y = y
        elif isinstance(x, Point2D):
            self.x = x.x
            self.y = x.y
        else:
            self.x = int(x)
            self.y = int(y)

    def __str__(self):
        if self.y == 0:
            return str(self.x)
        return f"{self.x}:{self.y}"

    def __eq__(self, other):
        if isinstance(other, Point2D):
            return self.x == other.x and self.y == other.y
        return self.x == other and self.y == 0

    def __gt__(self, other):
        if isinstance(other, Point2D):
            return self.x > other.x
        return self.x > other

    def __lt__(self, other):
        if isinstance(other, Point2D):
            return self.x < other.x
        return self.x < other

    def __add__(self, other):
        if isinstance(other, Point2D):
            return Point2D(self.x + other.x, self.y + other.y)
        return Point2D(self.x + other, self.y)

    def __radd__(self, other):
        return Point2D(other + self.x, self.y)

    def __sub__(self, other):
        if isinstance(other, Point2D):
            return Point2D(self.x - other.x, self.y - other.y)
        return Point2D(self.x - other, self.y)

    def __rsub__(self, other):
        return Point2D(other - self.x, -self.y)

    def __mul__(self, other):
        if isinstance(other, Point2D):
            return Point2D(self.x * other.x, self.y * other.y)
        return Point2D(self.x * other, self.y)

    def __rmul__(self, other):
        return Point2D(other * self.x, self.y)

    def __truediv__(self, other):
        if isinstance(other, Point2D):
            return Point2D(self.x // other.x, self.y)
        return Point2D(self.x // other, self.y)

    def __rtruediv__(self, other):
        return Point2D(other // self.x, 0)

    def __mod__(self, other):
        if isinstance(other, Point2D):
            return Point2D(self.x % other.x, self.y)
        return Point2D(self.x % other, self.y)

    def __rmod__(self, other):
        return Point2D(other % self.x, 0)

    def __int__(self):
        return self.x

    def __index__(self):
        return int(self.x)

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"{self.x}:{self.y}"
    
class Warrior(object):
    "An encapsulation of a Redcode Warrior, with instructions and meta-data"

    def __init__(self, name='Unnamed', author='Anonymous', date=None,
                 version=None, strategy=None, start=Point2D(0)):
        self.name = name
        self.author = author
        self.date = date
        self.version = version
        self.strategy = strategy
        self.start = start
        self.instructions = {}  # Map of Point2D -> Instruction
        self.task_queue = []

    def __iter__(self):
        return iter(self.instructions.items())

    def __len__(self):
        return len(self.instructions)

    def __repr__(self):
        return "<Warrior %s by %s>" % (self.name, self.instructions)

    def get_bounds(self):
        """Get the bounds of the warrior's instructions in 2D space."""
        if not self.instructions:
            return Point2D(0, 0), Point2D(0, 0)
        
        min_x = min(p.x for p in self.instructions.keys())
        max_x = max(p.x for p in self.instructions.keys())
        min_y = min(p.y for p in self.instructions.keys())
        max_y = max(p.y for p in self.instructions.keys())
        
        return Point2D(min_x, min_y), Point2D(max_x, max_y)

    def get_size(self):
        """Get the size of the warrior in 2D space."""
        min_point, max_point = self.get_bounds()
        return Point2D(max_point.x - min_point.x + 1, max_point.y - min_point.y + 1)

class Instruction(object):
    "An encapsulation of a Redcode instruction."

    def __init__(self, opcode, modifier=None, stepping=None, a_mode=None, a_number=0,
                 b_mode=None, b_number=0, energy=0):
        self.opcode = OPCODES[opcode.upper()] if isinstance(opcode, str) else opcode
        self.modifier = MODIFIERS[modifier.upper()] if isinstance(modifier, str) else modifier
        # Only convert stepping to uppercase if it's a string and not a mode character
        if isinstance(stepping, str) and stepping not in MODES:
            self.stepping = STEP_MODIFIERS[stepping.upper()]
        else:
            self.stepping = STEP_NORMAL if stepping is None else stepping
        if a_mode is not None:
            self.a_mode = MODES[a_mode] if isinstance(a_mode, str) else a_mode
        else:
            self.a_mode = DIRECT
        if b_mode is not None:
            self.b_mode = MODES[b_mode] if isinstance(b_mode, str) else b_mode
        else:
            self.b_mode = IMMEDIATE if self.opcode == DAT and a_number != None else DIRECT

        # Store symbolic values as strings
        self._a_number = a_number
        self._b_number = b_number

        self.energy = energy

        # Set default modifier if none provided
        if self.modifier is None:
            self.modifier = self.default_modifier()

        self.core = None
        self.fg_color = None
        self.bg_color = None

    def core_binded(self, core):
        """Return a copy of this instruction binded to a Core.
        """
        instruction = copy(self)
        instruction.core = core
        return instruction

    def normalize(self, size: int):
        if isinstance(self.a_number, Point2D):
            self.a_number.x %= size
            self.a_number.y %= size
        if isinstance(self.b_number, Point2D):
            self.b_number.x %= size
            self.b_number.y %= size

    def default_modifier(self):
        for opcodes, modes_modifiers in DEFAULT_MODIFIERS.items():
            if self.opcode in opcodes:
                for ab_modes, modifier in modes_modifiers.items():
                    a_modes, b_modes = ab_modes
                    if self.a_mode in a_modes and self.b_mode in b_modes:
                        return modifier
        raise RuntimeError("Error getting default modifier for instruction: %s" % self)

    @property
    def a_number(self):
        if isinstance(self._a_number, str):
            return self._a_number
        if isinstance(self._a_number, Point2D):
            return self._a_number
        if isinstance(self._a_number, str) and ':' in self._a_number:
            x, y = map(int, self._a_number.split(':'))
            return Point2D(x, y)
        return Point2D(int(self._a_number) if self._a_number else 0)

    @a_number.setter
    def a_number(self, value):
        if isinstance(value, Point2D):
            self._a_number = value
        elif isinstance(value, str) and ':' in value:
            x, y = map(int, value.split(':'))
            self._a_number = Point2D(x, y)
        else:
            self._a_number = Point2D(int(value) if value else 0)

    @property
    def b_number(self):
        if isinstance(self._b_number, str):
            return self._b_number
        if isinstance(self._b_number, Point2D):
            return self._b_number
        if isinstance(self._b_number, str) and ':' in self._b_number:
            x, y = map(int, self._b_number.split(':'))
            return Point2D(x, y)
        return Point2D(int(self._b_number) if self._b_number else 0)

    @b_number.setter
    def b_number(self, value):
        if isinstance(value, Point2D):
            self._b_number = value
        elif isinstance(value, str) and ':' in value:
            x, y = map(int, value.split(':'))
            self._b_number = Point2D(x, y)
        else:
            self._b_number = Point2D(int(value) if value else 0)

    def __eq__(self, other):
        return (self.opcode == other.opcode and self.modifier == other.modifier and
                self.a_mode == other.a_mode and self.a_number == other.a_number and
                self.b_mode == other.b_mode and self.b_number == other.b_number and
                self.stepping == other.stepping)

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        # inverse lookup the instruction values
        opcode_str = {v: k for k, v in OPCODES.items() if k.isupper() and isinstance(v, int)}.get(self.opcode, 'UNKNOWN')
        modifier_str = {v: k for k, v in MODIFIERS.items()}.get(self.modifier, str(self.modifier))
        stepping_str = {v: k for k, v in STEP_MODIFIERS.items()}.get(self.stepping, '')
        a_mode_str = next(key for key,value in MODES.items() if value==self.a_mode)
        b_mode_str = next(key for key,value in MODES.items() if value==self.b_mode)
        energy_str = f"; E:{self.energy}" if self.energy else ""
        # Only show stepping modifier if it's not the default (D)
        stepping_suffix = f".{stepping_str}" if stepping_str and stepping_str != 'D' else "  "
        return "%s.%s%s %s %s, %s %s%s" % (opcode_str,
                                       modifier_str.ljust(2),
                                       stepping_suffix,
                                       a_mode_str,
                                       str(self.a_number),
                                       b_mode_str,
                                       str(self.b_number),
                                       energy_str)

    def __repr__(self):
        return "<Instruction %s>" % self

    def has_energy(self):
        """Check if the instruction has energy to execute."""
        return self.energy > 0

    def consume_energy(self, amount=1):
        """Consume energy from the instruction."""
        print(f"Consuming energy from {self} with amount {amount}")
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False

    def move_energy(self, other_instruction):
        """Equalize energy between this instruction and another."""
        total_energy = self.energy + other_instruction.energy
        self.energy = total_energy // 2
        other_instruction.energy = total_energy - self.energy

def parse(input, definitions={}):
    """Parse Redcode from a line iterator returning a Warrior object."""
    from parser import parse as parse_warrior
    return parse_warrior(input, definitions)

