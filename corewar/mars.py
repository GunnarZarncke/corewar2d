#! /usr/bin/env python3
# coding: utf-8

from collections import deque
from copy import copy
import operator
from random import randint

from core import Core, DEFAULT_INITIAL_INSTRUCTION
from redcode import *
from redcode import STEP_NORMAL, STEP_VERTICAL, STEP_BACKWARD, STEP_VERTICAL_BACKWARD
from redcode import Point2D

__all__ = ['MARS', 'EVENT_EXECUTED', 'EVENT_I_WRITE', 'EVENT_I_READ',
           'EVENT_A_DEC', 'EVENT_A_INC', 'EVENT_B_DEC', 'EVENT_B_INC',
           'EVENT_A_READ', 'EVENT_A_WRITE', 'EVENT_B_READ', 'EVENT_B_WRITE',
           'EVENT_A_ARITH', 'EVENT_B_ARITH']

# Event types
EVENT_EXECUTED = 0
EVENT_I_WRITE  = 1
EVENT_I_READ   = 2
EVENT_A_DEC    = 3
EVENT_A_INC    = 4
EVENT_B_DEC    = 5
EVENT_B_INC    = 6
EVENT_A_READ   = 7
EVENT_A_WRITE  = 8
EVENT_B_READ   = 9
EVENT_B_WRITE  = 10
EVENT_A_ARITH  = 11
EVENT_B_ARITH  = 12

class MARS(object):
    """The MARS. Encapsulates a simulation.
    """

    def __init__(self, core=None, warriors=None, minimum_separation=100,
                 randomize=True, max_processes=None, total_energy=100000):
        self.core = core if core else Core()
        self.minimum_separation = minimum_separation
        self.max_processes = max_processes if max_processes else len(self.core)
        self.warriors = warriors if warriors else []
        self.energy_mode = total_energy > 0
        if self.warriors:
            self.load_warriors(randomize, total_energy)

    def point_to_index(self, point):
        """Convert a Point2D to a memory index, handling wrapping around the core size."""
        return self.core.point_to_index(point)

    def get_instruction(self, point):
        """Get instruction at Point2D coordinates."""
        return self.core[point]

    def set_instruction(self, point, instruction):
        """Set instruction at Point2D coordinates."""
        # Validate and normalize the instruction's values
        if not isinstance(instruction.a_number, Point2D):
            print(f"a_number type: {type(instruction.a_number)}, value: {instruction.a_number}")
            raise ValueError(f"a_number must be a Point2D, got {type(instruction.a_number)}, {Point2D.__module__}")
        if not isinstance(instruction.b_number, Point2D):
            print(f"b_number type: {type(instruction.b_number)}, value: {instruction.b_number}")
            raise ValueError(f"b_number must be a Point2D, got {type(instruction.b_number)}, {Point2D.__module__}")
        
        #instruction.a_number = self.core.normalize_point(instruction.a_number)
        #instruction.b_number = self.core.normalize_point(instruction.b_number)
        
        self.core[point] = instruction

    def core_event(self, warrior, address : Point2D, event_type):
        """Supposed to be implemented by subclasses to handle core
           events.
        """
        pass

    def reset(self, clear_instruction=DEFAULT_INITIAL_INSTRUCTION):
        "Clears core and re-loads warriors."
        self.core.clear(clear_instruction)
        self.load_warriors()

    def load_warriors(self, randomize=True, total_energy = 0):
        "Loads its warriors to the memory with starting task queues"

        # the space between warriors - equally spaced in the core
        space = len(self.core) // len(self.warriors)

        for n, warrior in enumerate(self.warriors):
            # Calculate base position using linear addressing
            base_pos = n * space
            
            # Convert to 2D coordinates using core width
            warrior_position = Point2D(base_pos % self.core.width, 
                                     base_pos // self.core.width)

            # Get warrior's grid size
            warrior_size = warrior.get_size()
            warrior_grid_size = warrior_size.x + warrior_size.y * self.core.width

            if randomize:
                # Randomize within the space, maintaining minimum separation
                max_offset = space - warrior_grid_size - self.minimum_separation
                if max_offset > 0:
                    offset = randint(0, max_offset)
                    # Convert offset to 2D coordinates
                    warrior_position = Point2D(
                        (base_pos + offset) % self.core.width,
                        (base_pos + offset) // self.core.width
                    )

            # Convert warrior's start position to 2D
            start_pos = Point2D(
                warrior_position.x + warrior.start.x,
                warrior_position.y + warrior.start.y
            )

            # Add first task
            warrior.task_queue = [start_pos]

            # Calculate energy per instruction for this warrior
            warrior_energy = total_energy // len(warrior.instructions) if self.energy_mode else 1000

            # Copy warrior's instructions to the core
            for pos, instruction in warrior.instructions.items():
                # Calculate absolute position in core
                abs_x = (warrior_position.x + pos.x) % self.core.width
                abs_y = (warrior_position.y + pos.y) % self.core.height
                abs_pos = Point2D(abs_x, abs_y)
                
                # Create a copy of the instruction with warrior's energy
                instruction_copy = copy(instruction)
                if self.energy_mode:
                    instruction_copy.energy = warrior_energy
                
                # Store instruction
                self.set_instruction(abs_pos, instruction_copy)
                self.core_event(warrior, abs_pos, EVENT_I_WRITE)

    def enqueue(self, warrior, point):
        """Enqueue another process into the warrior's task queue. Only if it's
           not already full.
        """
        if len(warrior.task_queue) < self.max_processes:
            if not isinstance(point, Point2D):
                raise ValueError(f"point must be a Point2D, got {type(point)}")
            # Handle negative addresses by wrapping them to positive
            point = self.core.trim(point)
            warrior.task_queue.append(point)

    def __iter__(self):
        return iter(self.core)

    def __len__(self):
        return len(self.core)

    def __getitem__(self, point):
        return self.get_instruction(point)

    def increment_by_stepping(self, point, amount, stepping):
        """Increment a point based on the stepping mode.
        
        Args:
            point: Point2D to increment
            amount: Amount to increment by (can be negative for decrement)
            stepping: Stepping mode to use
            
        Returns:
            Point2D: New incremented point
        """
        print(f"stepping: {stepping}, amount: {amount}, point: {point}")
        if stepping == STEP_NORMAL:
            return Point2D(point.x + amount, point.y)
        elif stepping == STEP_VERTICAL:
            return Point2D(point.x, point.y + amount)
        elif stepping == STEP_BACKWARD:
            return Point2D(point.x - amount, point.y)
        elif stepping == STEP_VERTICAL_BACKWARD:
            return Point2D(point.x, point.y - amount)
        else:
            raise ValueError(f"Invalid stepping mode: {stepping}")

    def evaluate_operand(self, pc, number, mode, stepping, warrior):
        """Evaluate an operand (A or B) and return (read_point, write_point, pip_point)."""
        if mode == IMMEDIATE:
            return Point2D(0), Point2D(0), None
        else:
            read_point = write_point = Point2D(number)
            pip_point = None

            if mode != DIRECT:
                pip_point = Point2D(pc.x + write_point.x, pc.y + write_point.y)

                # pre-decrement, if needed
                if mode == PREDEC_A:
                    instruction = self.get_instruction(pip_point)
                    instruction.a_number = self.increment_by_stepping(instruction.a_number, -1, stepping)
                    self.core_event(warrior, pip_point, EVENT_A_DEC)
                elif mode == PREDEC_B:
                    instruction = self.get_instruction(pip_point)
                    instruction.b_number = self.increment_by_stepping(instruction.b_number, -1, stepping)
                    self.core_event(warrior, pip_point, EVENT_B_DEC)

                # calculate the indirect address
                if mode in (PREDEC_A, INDIRECT_A, POSTINC_A):
                    read_point = Point2D(read_point.x + self.get_instruction(Point2D(pc.x + read_point.x, pc.y + read_point.y)).a_number, 0)
                    write_point = Point2D(write_point.x + self.get_instruction(Point2D(pc.x + write_point.x, pc.y + write_point.y)).a_number, 0)
                else: # B modes
                    read_point = Point2D(read_point.x + self.get_instruction(Point2D(pc.x + read_point.x, pc.y + read_point.y)).b_number, 0)
                    write_point = Point2D(write_point.x + self.get_instruction(Point2D(pc.x + write_point.x, pc.y + write_point.y)).b_number, 0)

                # post-increment is performed after operation by helper handle_post_increment()

            return read_point, write_point, pip_point

    def handle_post_increment(self, pip_point, mode, stepping, warrior):
        """Handle post-increment operations."""
        if pip_point is None:
            return

        instruction = self.get_instruction(pip_point)
        if mode == POSTINC_A:
            instruction.a_number = self.increment_by_stepping(instruction.a_number, 1, stepping)
            self.core_event(warrior, pip_point, EVENT_A_INC)
        elif mode == POSTINC_B:
            instruction.b_number = self.increment_by_stepping(instruction.b_number, 1, stepping)
            self.core_event(warrior, pip_point, EVENT_B_INC)

    def execute_instruction(self, warrior, pc, ir, ira, irb, rpa, rpb, wpb):
        """Execute a single instruction based on its opcode."""
        if ir.opcode == DAT:
            # does not enqueue next instruction, therefore, killing the process
            pass
        elif ir.opcode == MOV:
            self.execute_mov(warrior, pc, ir, ira, rpa, wpb)
        elif ir.opcode == ADD:
            self.do_arithmetic(warrior, pc, ir, ira, irb, rpa, rpb, wpb, operator.add)
        elif ir.opcode == SUB:
            self.do_arithmetic(warrior, pc, ir, ira, irb, rpa, rpb, wpb, operator.sub)
        elif ir.opcode == MUL:
            self.do_arithmetic(warrior, pc, ir, ira, irb, rpa, rpb, wpb, operator.mul)
        elif ir.opcode == DIV:
            self.do_arithmetic(warrior, pc, ir, ira, irb, rpa, rpb, wpb, operator.truediv)
        elif ir.opcode == MOD:
            self.do_arithmetic(warrior, pc, ir, ira, irb, rpa, rpb, wpb, operator.mod)
        elif ir.opcode == JMP:
            self.enqueue(warrior, Point2D(pc.x + rpa.x, pc.y + rpa.y))
        elif ir.opcode == JMZ:
            self.execute_jmz(warrior, pc, ir, irb, rpa)
        elif ir.opcode == JMN:
            self.execute_jmn(warrior, pc, ir, irb, rpa)
        elif ir.opcode == DJN:
            self.execute_djn(warrior, pc, ir, irb, rpa, wpb)
        elif ir.opcode == SPL:
            self.enqueue(warrior, self.increment_by_stepping(pc, 1, ir.stepping))
            self.enqueue(warrior, Point2D(pc.x + rpa.x, pc.y + rpa.y))
        elif ir.opcode == SLT:
            self.do_comparison(warrior, pc, ir, ira, irb, rpa, rpb, operator.lt)
        elif ir.opcode == CMP or ir.opcode == SEQ:
            self.do_comparison(warrior, pc, ir, ira, irb, rpa, rpb, operator.eq)
        elif ir.opcode == SNE:
            self.do_comparison(warrior, pc, ir, ira, irb, rpa, rpb, operator.ne)
        elif ir.opcode == NOP:
            self.enqueue(warrior, self.increment_by_stepping(pc, 1, ir.stepping))
        else:
            raise ValueError("Invalid opcode: %d" % ir.opcode)

    def normalize(self, number):
        """Normalize a number to the core size."""
        return number #% self.core.size

    def execute_mov(self, warrior, pc, ir, ira, rpa, wpb):
        """Execute a MOV instruction."""
        target_point = Point2D(pc.x + wpb.x, pc.y + wpb.y)
        target_instruction = self.get_instruction(target_point)
        rpa_point = Point2D(pc.x + rpa.x, pc.y + rpa.y)

        # Move energy between instructions if in energy mode
        if self.energy_mode:
            target_instruction.move_energy(ira)

        if ir.modifier == M_A:
            target_instruction.a_number = ira.a_number
            self.core_event(warrior, rpa_point, EVENT_A_READ)
            self.core_event(warrior, target_point, EVENT_A_WRITE)
        elif ir.modifier == M_B:
            target_instruction.b_number = ira.b_number
            self.core_event(warrior, rpa_point, EVENT_B_READ)
            self.core_event(warrior, target_point, EVENT_B_WRITE)
        elif ir.modifier == M_AB:
            target_instruction.b_number = ira.a_number
            self.core_event(warrior, rpa_point, EVENT_A_READ)
            self.core_event(warrior, target_point, EVENT_B_WRITE)
        elif ir.modifier == M_BA:
            target_instruction.a_number = ira.b_number
            self.core_event(warrior, rpa_point, EVENT_B_READ)
            self.core_event(warrior, target_point, EVENT_A_WRITE)
        elif ir.modifier == M_F:
            target_instruction.a_number = ira.a_number
            target_instruction.b_number = ira.b_number
            self.core_event(warrior, rpa_point, EVENT_A_READ)
            self.core_event(warrior, rpa_point, EVENT_B_READ)
            self.core_event(warrior, target_point, EVENT_A_WRITE)
            self.core_event(warrior, target_point, EVENT_B_WRITE)
        elif ir.modifier == M_X:
            target_instruction.b_number = ira.a_number
            target_instruction.a_number = ira.b_number
            self.core_event(warrior, rpa_point, EVENT_A_READ)
            self.core_event(warrior, rpa_point, EVENT_B_READ)
            self.core_event(warrior, target_point, EVENT_A_WRITE)
            self.core_event(warrior, target_point, EVENT_B_WRITE)
        elif ir.modifier == M_I:
            self.set_instruction(target_point, ira)
            self.core_event(warrior, rpa_point, EVENT_I_READ)
            self.core_event(warrior, target_point, EVENT_I_WRITE)
        else:
            raise ValueError("Invalid modifier: %d" % ir.modifier)

        self.enqueue(warrior, self.increment_by_stepping(pc, 1, ir.stepping))

    def execute_jmz(self, warrior, pc, ir, irb, rpa):
        """Execute a JMZ instruction."""
        rpa_point = Point2D(pc.x + rpa.x, pc.y + rpa.y)
        next_point = self.increment_by_stepping(pc, 1, ir.stepping)

        if ir.modifier == M_A or ir.modifier == M_BA:
            self.enqueue(warrior, rpa_point if irb.a_number == 0 else next_point)
            self.core_event(warrior, rpa_point, EVENT_A_READ)
        elif ir.modifier == M_B or ir.modifier == M_AB:
            self.enqueue(warrior, rpa_point if irb.b_number == 0 else next_point)
            self.core_event(warrior, rpa_point, EVENT_B_READ)
        elif ir.modifier in (M_F, M_X, M_I):
            self.enqueue(warrior, rpa_point if irb.a_number == irb.b_number == 0 else next_point)
            self.core_event(warrior, rpa_point, EVENT_A_READ)
            self.core_event(warrior, rpa_point, EVENT_B_READ)
        else:
            raise ValueError("Invalid modifier: %d" % ir.modifier)

    def execute_jmn(self, warrior, pc, ir, irb, rpa):
        """Execute a JMN instruction."""
        rpa_point = Point2D(pc.x + rpa.x, pc.y + rpa.y)
        next_point = self.increment_by_stepping(pc, 1, ir.stepping)

        if ir.modifier == M_A or ir.modifier == M_BA:
            self.enqueue(warrior, rpa_point if irb.a_number != 0 else next_point)
            self.core_event(warrior, rpa_point, EVENT_A_READ)
        elif ir.modifier == M_B or ir.modifier == M_AB:
            self.enqueue(warrior, rpa_point if irb.b_number != 0 else next_point)
            self.core_event(warrior, rpa_point, EVENT_B_READ)
        elif ir.modifier in (M_F, M_X, M_I):
            self.enqueue(warrior, rpa_point if irb.a_number != 0 or irb.b_number != 0 else next_point)
            self.core_event(warrior, rpa_point, EVENT_A_READ)
            self.core_event(warrior, rpa_point, EVENT_B_READ)
        else:
            raise ValueError("Invalid modifier: %d" % ir.modifier)

    def execute_djn(self, warrior, pc, ir, irb, rpa, wpb):
        """Execute a DJN instruction."""
        target_point = Point2D(pc.x + wpb.x, pc.y + wpb.y)
        rpa_point = Point2D(pc.x + rpa.x, pc.y + rpa.y)
        next_point = self.increment_by_stepping(pc, 1, ir.stepping)

        if ir.modifier == M_A or ir.modifier == M_BA:
            self.get_instruction(target_point).a_number -= 1
            irb.a_number -= 1
            self.enqueue(warrior, rpa_point if irb.a_number != 0 else next_point)
            self.core_event(warrior, rpa_point, EVENT_A_READ)
            self.core_event(warrior, rpa_point, EVENT_A_DEC)
        elif ir.modifier == M_B or ir.modifier == M_AB:
            self.get_instruction(target_point).b_number -= 1
            irb.b_number -= 1
            self.enqueue(warrior, rpa_point if irb.b_number != 0 else next_point)
            self.core_event(warrior, rpa_point, EVENT_B_READ)
            self.core_event(warrior, rpa_point, EVENT_B_DEC)
        elif ir.modifier in (M_F, M_X, M_I):
            self.get_instruction(target_point).a_number -= 1
            irb.a_number -= 1
            self.get_instruction(target_point).b_number -= 1
            irb.b_number -= 1
            self.enqueue(warrior, rpa_point if irb.a_number != 0 or irb.b_number != 0 else next_point)
            self.core_event(warrior, rpa_point, EVENT_A_READ)
            self.core_event(warrior, rpa_point, EVENT_B_READ)
            self.core_event(warrior, rpa_point, EVENT_A_DEC)
            self.core_event(warrior, rpa_point, EVENT_B_DEC)
        else:
            raise ValueError("Invalid modifier: %d" % ir.modifier)

    def step(self):
        """Run one simulation step: execute one task of every active warrior."""
        for warrior in self.warriors:
            if warrior.task_queue:
                # The process counter is the next instruction-address in the
                # warrior's task queue
                pc = warrior.task_queue.pop(0)
                #print(f"pc: {pc}")
                if not isinstance(pc, Point2D):
                    raise ValueError("Invalid process counter: %s" % pc)

                # Get the current instruction
                ir = self.get_instruction(pc)

                # Check energy if in energy mode
                if self.energy_mode and not ir.has_energy():
                    continue  # Skip execution if no energy

                # copy the current instruction to the instruction register
                ir = copy(ir)

                # evaluate the A-operand
                rpa, wpa, pip_a = self.evaluate_operand(pc, ir.a_number, ir.a_mode, ir.stepping, warrior)
                ira = copy(self.get_instruction(Point2D(pc.x + rpa.x, pc.y + rpa.y)))
                self.handle_post_increment(pip_a, ir.a_mode, ir.stepping, warrior)

                # evaluate the B-operand
                rpb, wpb, pip_b = self.evaluate_operand(pc, ir.b_number, ir.b_mode, ir.stepping, warrior)
                irb = copy(self.get_instruction(Point2D(pc.x + rpb.x, pc.y + rpb.y)))
                self.handle_post_increment(pip_b, ir.b_mode, ir.stepping, warrior)

                # Consume energy if in energy mode
                if self.energy_mode:
                    if not ir.consume_energy():
                        continue  # Skip execution if not enough energy

                self.core_event(warrior, pc, EVENT_EXECUTED)
                self.execute_instruction(warrior, pc, ir, ira, irb, rpa, rpb, wpb)

    def do_arithmetic(self, warrior, pc, ir, ira, irb, rpa, rpb, wpb, op):
        """Execute arithmetic operations (ADD, SUB, MUL, DIV, MOD)."""
        try:
            # Pre-calculate common points and instructions
            target_point = Point2D(pc.x + wpb.x, pc.y + wpb.y)
            target_instruction = self.get_instruction(target_point)
            rpa_point = Point2D(pc.x + rpa.x, pc.y + rpa.y)
            rpb_point = Point2D(pc.x + rpb.x, pc.y + rpb.y)

            if ir.modifier == M_A:
                target_instruction.a_number = self.normalize(op(irb.a_number, ira.a_number))
                self.core_event(warrior, target_point, EVENT_A_WRITE)
                self.core_event(warrior, rpa_point, EVENT_A_READ)
                self.core_event(warrior, rpb_point, EVENT_A_READ)
            elif ir.modifier == M_B:
                target_instruction.b_number = self.normalize(op(irb.b_number, ira.b_number))
                self.core_event(warrior, target_point, EVENT_B_WRITE)
                self.core_event(warrior, rpa_point, EVENT_B_READ)
                self.core_event(warrior, rpb_point, EVENT_B_READ)
            elif ir.modifier == M_AB:
                target_instruction.b_number = self.normalize(op(irb.b_number, ira.a_number))
                self.core_event(warrior, target_point, EVENT_B_WRITE)
                self.core_event(warrior, rpa_point, EVENT_A_READ)
                self.core_event(warrior, rpb_point, EVENT_B_READ)
            elif ir.modifier == M_BA:
                target_instruction.a_number = self.normalize(op(irb.b_number, ira.a_number))
                self.core_event(warrior, target_point, EVENT_A_WRITE)
                self.core_event(warrior, rpa_point, EVENT_A_READ)
                self.core_event(warrior, rpb_point, EVENT_B_READ)
            elif ir.modifier == M_F or ir.modifier == M_I:
                target_instruction.a_number = self.normalize(op(irb.a_number, ira.a_number))
                target_instruction.b_number = self.normalize(op(irb.b_number, ira.b_number))
                self.core_event(warrior, target_point, EVENT_A_WRITE)
                self.core_event(warrior, target_point, EVENT_B_WRITE)
                self.core_event(warrior, rpa_point, EVENT_A_READ)
                self.core_event(warrior, rpb_point, EVENT_A_READ)
                self.core_event(warrior, rpa_point, EVENT_B_READ)
                self.core_event(warrior, rpb_point, EVENT_B_READ)
            elif ir.modifier == M_X:
                target_instruction.b_number = self.normalize(op(irb.b_number, ira.a_number))
                target_instruction.a_number = self.normalize(op(irb.a_number, ira.b_number))
                self.core_event(warrior, target_point, EVENT_A_WRITE)
                self.core_event(warrior, target_point, EVENT_B_WRITE)
                self.core_event(warrior, rpa_point, EVENT_A_READ)
                self.core_event(warrior, rpb_point, EVENT_A_READ)
                self.core_event(warrior, rpa_point, EVENT_B_READ)
                self.core_event(warrior, rpb_point, EVENT_B_READ)
            else:
                raise ValueError("Invalid modifier: %d" % ir.modifier)

            self.enqueue(warrior, self.increment_by_stepping(pc, 1, ir.stepping))
        except ZeroDivisionError:
            # In case of division by zero, the process is killed
            pass

    def do_comparison(self, warrior, pc, ir, ira, irb, rpa, rpb, cmp):
        """Execute comparison operations (SLT, CMP/SEQ, SNE)."""
        # Pre-calculate common points
        rpa_point = Point2D(pc.x + rpa.x, pc.y + rpa.y)
        rpb_point = Point2D(pc.x + rpb.x, pc.y + rpb.y)
        next_point = self.increment_by_stepping(pc, 1, ir.stepping)
        jump_point = self.increment_by_stepping(pc, 2, ir.stepping)

        if ir.modifier == M_A:
            result = cmp(ira.a_number, irb.a_number)
            self.enqueue(warrior, jump_point if result else next_point)
            self.core_event(warrior, rpa_point, EVENT_A_READ)
            self.core_event(warrior, rpb_point, EVENT_A_READ)
        elif ir.modifier == M_B:
            result = cmp(ira.b_number, irb.b_number)
            self.enqueue(warrior, jump_point if result else next_point)
            self.core_event(warrior, rpa_point, EVENT_B_READ)
            self.core_event(warrior, rpb_point, EVENT_B_READ)
        elif ir.modifier == M_AB:
            result = cmp(ira.a_number, irb.b_number)
            self.enqueue(warrior, jump_point if result else next_point)
            self.core_event(warrior, rpa_point, EVENT_A_READ)
            self.core_event(warrior, rpb_point, EVENT_B_READ)
        elif ir.modifier == M_BA:
            result = cmp(ira.b_number, irb.a_number)
            self.enqueue(warrior, jump_point if result else next_point)
            self.core_event(warrior, rpa_point, EVENT_B_READ)
            self.core_event(warrior, rpb_point, EVENT_A_READ)
        elif ir.modifier == M_F:
            result = cmp(ira.a_number, irb.a_number) and cmp(ira.b_number, irb.b_number)
            self.enqueue(warrior, jump_point if result else next_point)
            self.core_event(warrior, rpa_point, EVENT_A_READ)
            self.core_event(warrior, rpb_point, EVENT_A_READ)
            self.core_event(warrior, rpa_point, EVENT_B_READ)
            self.core_event(warrior, rpb_point, EVENT_B_READ)
        elif ir.modifier == M_X:
            result = cmp(ira.a_number, irb.b_number) and cmp(ira.b_number, irb.a_number)
            self.enqueue(warrior, jump_point if result else next_point)
            self.core_event(warrior, rpa_point, EVENT_A_READ)
            self.core_event(warrior, rpb_point, EVENT_A_READ)
            self.core_event(warrior, rpa_point, EVENT_B_READ)
            self.core_event(warrior, rpb_point, EVENT_B_READ)
        elif ir.modifier == M_I:
            result = ira == irb
            self.enqueue(warrior, jump_point if result else next_point)
            self.core_event(warrior, rpa_point, EVENT_I_READ)
            self.core_event(warrior, rpb_point, EVENT_I_READ)
        else:
            raise ValueError("Invalid modifier: %d" % ir.modifier)

if __name__ == "__main__":
    import argparse
    import redcode

    parser = argparse.ArgumentParser(description='MARS (Memory Array Redcode Simulator)')
    parser.add_argument('--rounds', '-r', metavar='ROUNDS', type=int, nargs='?',
                        default=1, help='Rounds to play')
    parser.add_argument('--size', '-s', metavar='CORESIZE', type=int, nargs='?',
                        default=8000, help='The core size')
    parser.add_argument('--cycles', '-c', metavar='CYCLES', type=int, nargs='?',
                        default=80000, help='Cycles until tie')
    parser.add_argument('--processes', '-p', metavar='MAXPROCESSES', type=int, nargs='?',
                        default=8000, help='Max processes')
    parser.add_argument('--length', '-l', metavar='MAXLENGTH', type=int, nargs='?',
                        default=100, help='Max warrior length')
    parser.add_argument('--distance', '-d', metavar='MINDISTANCE', type=int, nargs='?',
                        default=100, help='Minimum warrior distance')
    parser.add_argument('--energy', '-e', metavar='TOTAL_ENERGY', type=int, nargs='?',
                        const=100000, default=0, help='Total energy for simulation (default: 100000 when flag is present, 0 when flag is not present)')
    parser.add_argument('warriors', metavar='WARRIOR', type=str, nargs='+',
                        help='Warrior redcode filename')

    args = parser.parse_args()

    # build environment
    environment = {'CORESIZE': args.size,
                   'CYCLES': args.cycles,
                   'ROUNDS': args.rounds,
                   'MAXPROCESSES': args.processes,
                   'MAXLENGTH': args.length,
                   'MINDISTANCE': args.distance}

    # assemble warriors
    warriors = [redcode.parse(open(file, 'r'), environment) for file in args.warriors]

    # initialize wins, losses and ties for each warrior
    for warrior in warriors:
        warrior.wins = warrior.ties = warrior.losses = 0

    # for each round
    for i in range(args.rounds):
        # create new simulation
        simulation = MARS(warriors=warriors,
                          minimum_separation = args.distance,
                          max_processes = args.processes,
                          total_energy = args.energy)

        active_warrior_to_stop = 1 if len(warriors) >= 2 else 0

        for c in range(args.cycles):
            simulation.step()

            # if there's only one left, or are all dead, then stop simulation
            if sum(1 if warrior.task_queue else 0 for warrior in warriors) <= active_warrior_to_stop:
                for warrior in warriors:
                    if warrior.task_queue:
                        warrior.wins += 1
                    else:
                        warrior.losses += 1
                break
        else:
            # running until max cycles: tie
            for warrior in warriors:
                if warrior.task_queue:
                    warrior.ties += 1
                else:
                    warrior.losses += 1

    # print results
    print("Results: (%d rounds)" % args.rounds)
    print("%s %s %s %s" % ("Warrior (Author)".ljust(40), "wins".rjust(5),
                           "ties".rjust(5), "losses".rjust(5)))
    for warrior in warriors:
        print("%s %s %s %s" % (("%s (%s)" % (warrior.name, warrior.author)).ljust(40),
                               str(warrior.wins).rjust(5),
                               str(warrior.ties).rjust(5),
                               str(warrior.losses).rjust(5)))


