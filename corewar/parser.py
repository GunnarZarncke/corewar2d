from copy import copy
import re
from typing import Dict, Set, Tuple, Optional, Iterator
from redcode import (
    Warrior, Instruction, Point2D, OPCODES, MODIFIERS, 
    STEP_MODIFIERS, MODES, INSTRUCTION_REGEX, STEP_NORMAL,
    STEP_VERTICAL, STEP_BACKWARD, STEP_VERTICAL_BACKWARD,
    DAT, IMMEDIATE, DIRECT
)

class Parser:
    def __init__(self, definitions: Dict = None):
        self.definitions = definitions or {}
        self.labels: Dict[str, Point2D] = {}
        self.current_pos = Point2D(0, 0)
        self.used_positions: Set[Point2D] = set()
        self.environment = copy(self.definitions)
        self.found_redcode_info = False

    def parse(self, input_lines: Iterator[str]) -> Warrior:
        """Parse Redcode from a line iterator returning a Warrior object."""
        warrior = Warrior()
        warrior.strategy = []

        for n, line in enumerate(input_lines):
            line = line.strip()
            if not line:
                continue

            if self._handle_redcode_info(line, warrior, n):
                continue

            if self._handle_metadata(line, warrior):
                continue

            if self._handle_assert(line, n):
                continue

            # Remove comments
            line = self._strip_comments(line)
            if not line:
                continue

            if self._handle_org(line, warrior):
                continue

            if self._handle_end(line, warrior):
                break

            if self._handle_equ(line):
                continue

            # Handle labels and instruction
            line = self._handle_labels(line)
            self._parse_instruction(line, warrior, n)

        # Post-processing
        warrior.strategy = '\n'.join(warrior.strategy)
        self._evaluate_start(warrior)
        self._evaluate_labels(warrior)
        
        warrior.labels = self.labels
        warrior.environment = self.environment
        
        return warrior

    def _handle_redcode_info(self, line: str, warrior: Warrior, line_num: int) -> bool:
        """Handle ;redcode info comment."""
        m = re.match(r'^;redcode\w*$', line, re.I)
        if m:
            if self.found_redcode_info:
                return True  # Stop reading
            else:
                # Reset state for first ;redcode
                warrior.instructions = {}
                self.labels = {}
                self.environment = copy(self.definitions)
                self.current_pos = Point2D(0, 0)
                self.used_positions = set()
                self.found_redcode_info = True
            return True
        return False

    def _handle_metadata(self, line: str, warrior: Warrior) -> bool:
        """Handle metadata comments (name, author, etc.)."""
        metadata_patterns = {
            r'^;name\s+(.+)$': ('name', str),
            r'^;author\s+(.+)$': ('author', str),
            r'^;date\s+(.+)$': ('date', str),
            r'^;version\s+(.+)$': ('version', str),
            r'^;strat(?:egy)?\s+(.+)$': ('strategy', list)
        }

        for pattern, (attr, type_) in metadata_patterns.items():
            m = re.match(pattern, line, re.I)
            if m:
                value = m.group(1).strip()
                if type_ == list:
                    getattr(warrior, attr).append(value)
                else:
                    setattr(warrior, attr, value)
                return True
        return False

    def _handle_assert(self, line: str, line_num: int) -> bool:
        """Handle assert expressions."""
        m = re.match(r'^;assert\s+(.+)$', line, re.I)
        if m:
            if not eval(m.group(1), self.environment):
                raise AssertionError(f"Assertion failed: {line}, line {line_num}")
            return True
        return False

    def _strip_comments(self, line: str) -> str:
        """Remove comments from a line."""
        m = re.match(r'^([^;]*)\s*;', line)
        if m:
            line = m.group(1).strip()
        return line

    def _handle_org(self, line: str, warrior: Warrior) -> bool:
        """Handle ORG directive."""
        m = re.match(r'^ORG\s+(.+)\s*$', line, re.I)
        if m:
            warrior.start = m.group(1)
            return True
        return False

    def _handle_end(self, line: str, warrior: Warrior) -> bool:
        """Handle END directive."""
        m = re.match(r'^END(?:\s+([^\s]+))?$', line, re.I)
        if m:
            if m.group(1):
                warrior.start = m.group(1)
            return True
        return False

    def _handle_equ(self, line: str) -> bool:
        """Handle EQU directive."""
        m = re.match(r'^([a-z]\w*)\s+EQU\s+(.*)\s*$', line, re.I)
        if m:
            name, value = m.groups()
            self.environment[name] = eval(value, self.environment)
            return True
        return False

    def _handle_labels(self, line: str) -> str:
        """Handle labels and return remaining line."""
        while True:
            m = re.match(r'^([a-z]\w*)\s+(.+)\s*$', line)
            if m:
                label_candidate = m.group(1)
                if label_candidate.upper() not in OPCODES:
                    self.labels[label_candidate] = self.current_pos
                    line = m.group(2)
                    continue
            break
        return line

    def _parse_instruction(self, line: str, warrior: Warrior, line_num: int) -> None:
        """Parse a single instruction."""
        m = INSTRUCTION_REGEX.match(line)
        if not m:
            raise ValueError(f'Error at line {line_num}: expected instruction in expression: "{line}"')

        opcode, modifier, stepping, a_mode, a_number, b_mode, b_number, energy = m.groups()
        
        self._validate_instruction_components(opcode, modifier, stepping, line_num)
        
        print("DEBUG: Parsed instruction components:")
        print(f"  opcode:   {opcode}")
        print(f"  modifier: {modifier}")
        print(f"  stepping: {stepping}")
        print(f"  a_mode:   {a_mode}")
        print(f"  a_number: {a_number}")
        print(f"  b_mode:   {b_mode}")
        print(f"  b_number: {b_number}")
        print(f"  energy:   {energy}")

        if self.current_pos in self.used_positions:
            raise ValueError(f'Error at line {line_num}: instruction position {self.current_pos} already used')

        # Parse values
        a_number = self._parse_number(a_number)
        b_number = self._parse_number(b_number)
        energy_value = int(energy) if energy else None

        # Create and store instruction
        instruction = Instruction(
            opcode, modifier, stepping,
            a_mode, a_number,
            b_mode, b_number,
            energy=energy_value
        )
        warrior.instructions[self.current_pos] = instruction
        self.used_positions.add(self.current_pos)

        # Update position based on stepping
        self._update_position(stepping)

    def _validate_instruction_components(self, opcode: str, modifier: str, stepping: str, line_num: int) -> None:
        """Validate instruction components."""
        if opcode.upper() not in OPCODES:
            raise ValueError(f'Invalid opcode: {opcode} in line {line_num}')
        if modifier is not None and modifier.upper() not in MODIFIERS:
            raise ValueError(f'Invalid modifier: {modifier} in line {line_num}')
        if stepping is not None and stepping.upper() not in STEP_MODIFIERS:
            raise ValueError(f'Invalid stepping modifier: {stepping} in line {line_num}')

    def _parse_number(self, value: Optional[str]) -> Point2D:
        """Parse a number value into Point2D."""
        try:
            return Point2D(value)
        except:
            return value

    def _update_position(self, stepping: Optional[str]) -> None:
        """Update current position based on stepping mode."""
        stepping_mode = STEP_MODIFIERS[stepping.upper()] if stepping else STEP_NORMAL
        if stepping_mode == STEP_NORMAL:
            self.current_pos = Point2D(self.current_pos.x + 1, self.current_pos.y)
        elif stepping_mode == STEP_VERTICAL:
            self.current_pos = Point2D(self.current_pos.x, self.current_pos.y + 1)
        elif stepping_mode == STEP_BACKWARD:
            self.current_pos = Point2D(self.current_pos.x - 1, self.current_pos.y)
        elif stepping_mode == STEP_VERTICAL_BACKWARD:
            self.current_pos = Point2D(self.current_pos.x, self.current_pos.y - 1)

    def _evaluate_start(self, warrior: Warrior) -> None:
        """Evaluate start expression."""
        if isinstance(warrior.start, str):
            warrior.start = eval(warrior.start, self.environment, self.labels)
        if isinstance(warrior.start, int):
            warrior.start = Point2D(warrior.start, 0)

    def _evaluate_labels(self, warrior: Warrior) -> None:
        """Evaluate labels and expressions in instructions."""
        for pos, instruction in warrior.instructions.items():
            relative_labels = {
                name: Point2D(address.x - pos.x, address.y - pos.y)
                for name, address in self.labels.items()
            }

            if isinstance(instruction.a_number, str):
                instruction.a_number = eval(instruction.a_number, self.environment, relative_labels)
            if isinstance(instruction.b_number, str):
                instruction.b_number = eval(instruction.b_number, self.environment, relative_labels)

def parse(input_lines: Iterator[str], definitions: Dict = None) -> Warrior:
    """Parse Redcode from a line iterator returning a Warrior object."""
    parser = Parser(definitions)
    return parser.parse(input_lines) 