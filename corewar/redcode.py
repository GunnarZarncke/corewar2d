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
                               r'(?:\s*,\s*([#\$\*@\{<\}>])?\s*(.+))?$', # optional second value
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
                 b_mode=None, b_number=0):
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
        raise RuntimeError("Error getting default modifier")

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

        # Only show stepping modifier if it's not the default (D)
        stepping_suffix = f".{stepping_str}" if stepping_str and stepping_str != 'D' else "  "
        return "%s.%s%s %s %s, %s %s" % (opcode_str,
                                       modifier_str.ljust(2),
                                       stepping_suffix,
                                       a_mode_str,
                                       str(self.a_number),
                                       b_mode_str,
                                       str(self.b_number))

    def __repr__(self):
        return "<Instruction %s>" % self

def parse(input, definitions={}):
    """ Parse a Redcode code from a line iterator (input) returning a Warrior
        object."""

    found_recode_info_comment = False
    labels = {}
    current_pos = Point2D(0, 0)  # Track current position in 2D space
    used_positions = set()  # Track used positions to detect overlaps

    warrior = Warrior()
    warrior.strategy = []

    # use a version of environment because we're going to add names to it
    environment = copy(definitions)

    # first pass
    for n, line in enumerate(input):
        line = line.strip()
        if line:
            # process info comments
            m = re.match(r'^;redcode\w*$', line, re.I)
            if m:
                if found_recode_info_comment:
                    # stop reading, found second ;redcode
                    break;
                else:
                    # first ;redcode ignore all input before
                    warrior.instructions = {}
                    labels = {}
                    environment = copy(definitions)
                    current_pos = Point2D(0, 0)
                    used_positions = set()
                    found_recode_info_comment = True
                continue

            m = re.match(r'^;name\s+(.+)$', line, re.I)
            if m:
                warrior.name = m.group(1).strip()
                continue

            m = re.match(r'^;author\s+(.+)$', line, re.I)
            if m:
                warrior.author = m.group(1).strip()
                continue

            m = re.match(r'^;date\s+(.+)$', line, re.I)
            if m:
                warrior.date = m.group(1).strip()
                continue

            m = re.match(r'^;version\s+(.+)$', line, re.I)
            if m:
                warrior.version = m.group(1).strip()
                continue

            m = re.match(r'^;strat(?:egy)?\s+(.+)$', line, re.I)
            if m:
                warrior.strategy.append(m.group(1).strip())
                continue

            # Test if assert expression evaluates to true
            m = re.match(r'^;assert\s+(.+)$', line, re.I)
            if m:
                if not eval(m.group(1), environment):
                    raise AssertionError("Assertion failed: %s, line %d" % (line, n))
                continue

            # ignore other comments
            m = re.match(r'^([^;]*)\s*;', line)
            if m:
                # rip off comment from the line
                line = m.group(1).strip()
                # if this is a comment line
                if not line: continue

            # Match ORG
            m = re.match(r'^ORG\s+(.+)\s*$', line, re.I)
            if m:
                warrior.start = m.group(1)
                continue

            # Match END
            m = re.match(r'^END(?:\s+([^\s]+))?$', line, re.I)
            if m:
                if m.group(1):
                    warrior.start = m.group(1)
                break # stop processing (end of redcode)

            # Match EQU
            m = re.match(r'^([a-z]\w*)\s+EQU\s+(.*)\s*$', line, re.I)
            if m:
                name, value = m.groups()
                # evaluate EQU expression using previous EQU definitions,
                # add result to a name variable in environment
                environment[name] = eval(value, environment)
                continue

            # Keep matching the first word until it's no label anymore
            while True:
                m = re.match(r'^([a-z]\w*)\s+(.+)\s*$', line)
                if m:
                    label_candidate = m.group(1)
                    if label_candidate.upper() not in OPCODES:
                        labels[label_candidate] = current_pos

                        # strip label off and keep looking
                        line = m.group(2)
                        continue
                # its an instruction, not label. proceed OR no match, probably
                # a all-value-omitted instruction.
                break

            # At last, it should match an instruction
            m = INSTRUCTION_REGEX.match(line)
            if not m:
                raise ValueError('Error at line %d: expected instruction in expression: "%s"' %
                                 (n, line))
            else:
                opcode, modifier, stepping, a_mode, a_number, b_mode, b_number = m.groups()
                #print("DEBUG: Parsed instruction components:")
                #print(f"  opcode: {opcode}")
                #print(f"  modifier: {modifier}")
                #print(f"  stepping: {stepping}")
                #print(f"  a_mode: {a_mode}")
                #print(f"  a_number: {a_number}")
                #print(f"  b_mode: {b_mode}")
                #print(f"  b_number: {b_number}")

                if opcode.upper() not in OPCODES:
                    raise ValueError('Invalid opcode: %s in line %d: "%s"' %
                                     (opcode, n, line))
                if modifier is not None and modifier.upper() not in MODIFIERS:
                    raise ValueError('Invalid modifier: %s in line %d: "%s"' %
                                     (modifier, n, line))
                if stepping is not None and stepping.upper() not in STEP_MODIFIERS:
                    raise ValueError('Invalid stepping modifier: %s in line %d: "%s"' %
                                     (stepping, n, line))

                # Check if position is already used
                if current_pos in used_positions:
                    raise ValueError(f'Error at line {n}: instruction position {current_pos} already used')

                # Parse Point2D values if present
                try:
                    a_number = Point2D(a_number)
                except:
                    pass
                
                try:
                    b_number = Point2D(b_number)
                except:
                    pass

                # Create instruction and store at current position
                instruction = Instruction(opcode, modifier, stepping,
                                       a_mode, a_number,
                                       b_mode, b_number)
                warrior.instructions[current_pos] = instruction
                used_positions.add(current_pos)

                # Calculate next position based on stepping mode
                stepping_mode = STEP_MODIFIERS[stepping.upper()] if stepping else STEP_NORMAL
                if stepping_mode == STEP_NORMAL:
                    current_pos = Point2D(current_pos.x + 1, current_pos.y)
                elif stepping_mode == STEP_VERTICAL:
                    current_pos = Point2D(current_pos.x, current_pos.y + 1)
                elif stepping_mode == STEP_BACKWARD:
                    current_pos = Point2D(current_pos.x - 1, current_pos.y)
                elif stepping_mode == STEP_VERTICAL_BACKWARD:
                    current_pos = Point2D(current_pos.x, current_pos.y - 1)

    # join strategy lines with line breaks
    warrior.strategy = '\n'.join(warrior.strategy)

    # evaluate start expression
    if isinstance(warrior.start, str):
        warrior.start = eval(warrior.start, environment, labels)
    if isinstance(warrior.start, int):
        warrior.start = Point2D(warrior.start, 0)

    # second pass - evaluate labels and expressions
    for pos, instruction in warrior.instructions.items():
        # create a dictionary of relative labels addresses to be used as a local
        # eval environment
        relative_labels = dict((name, Point2D(address.x - pos.x, address.y - pos.y)) 
                             for name, address in labels.items())

        # evaluate instruction fields using global environment and labels
        if isinstance(instruction.a_number, str):
            instruction.a_number = eval(instruction.a_number, environment, relative_labels)
        if isinstance(instruction.b_number, str):
            instruction.b_number = eval(instruction.b_number, environment, relative_labels)

    warrior.labels = labels
    warrior.environment = environment

    return warrior

