#! /usr/bin/env python3
# coding: utf-8

from copy import copy
from redcode import Instruction, Point2D

__all__ = ['DEFAULT_INITIAL_INSTRUCTION', 'Core', 'Point2D']

DEFAULT_INITIAL_INSTRUCTION = Instruction('DAT', 'F', '$', 0, '$', 0)


class Core(object):
    """The Core itself. An array-like object with a bunch of instructions and
       warriors, and tasks.
    """

    def __init__(self, initial_instruction=DEFAULT_INITIAL_INSTRUCTION,
                 size=8000, width=100, read_limit=None, write_limit=None):
        self.size = size
        self.width = width
        self.height = size // width
        if size % width != 0:
            raise ValueError("Core size must be divisible by width")
        self.write_limit = write_limit if write_limit else self.size
        self.read_limit = read_limit if read_limit else self.size
        self.clear()

    def clear(self, instruction=DEFAULT_INITIAL_INSTRUCTION):
        """Writes the same instruction thorough the entire core.
        """
        self.instructions = [instruction.core_binded(self) for i in range(self.size)]

    def point_to_index(self, point):
        """Convert a Point2D to a memory index, handling 2D wrapping."""
        if not isinstance(point, Point2D):
            import traceback
            traceback.print_stack()
            raise ValueError("Point2D expected")
        round_x = point.x // self.width    # how many times you wrapped in x
        x_new  = point.x % self.width

        raw_y = point.y + round_x
        round_y = point.y // self.height # how many times you wrapped in y
        final_y = raw_y % self.height

        final_x = (x_new + round_y) % self.width
        return final_y * self.width + final_x

    def trim_write(self, address):
        "Return the trimmed address to write, considering the write limit."
        return self._trim(address, self.write_limit)

    def trim_read(self, address):
        "Return the trimmed address to read, considering the read limit."
        return self._trim(address, self.read_limit)

    def trim(self, value):
        "Return a trimmed value to the bounds of the core size"
        round_x = value.x // self.width   # how many times you wrapped in x
        x_new  = value.x % self.width

        raw_y = value.y + round_x
        round_y = value.y // self.height # how many times you wrapped in y
        final_y = raw_y % self.height

        final_x = (x_new + round_y) % self.width
        return Point2D(final_x, final_y)

    def trim_signed(self, value):
        "Return a trimmed value to the bounds of -core size to +core size"
        round_x = value.x // self.width   # how many times you wrapped in x
        x_new  = value.x % self.width

        raw_y = value.y + round_x
        round_y = value.y // self.height # how many times you wrapped in y
        final_y = raw_y % self.height

        final_x = (x_new + round_y) % self.width
        return Point2D(final_x, final_y)

    def __getitem__(self, key):
        if isinstance(key, slice):
            start, stop = key.start, key.stop
            if start > stop:
                return self.instructions[start:] + self.instructions[:stop]
            else:
                return self.instructions[start:stop]
        else:
            return self.instructions[self.point_to_index(key)]

    def __setitem__(self, address, instruction):
        self.instructions[self.point_to_index(address)] = instruction

    def __iter__(self):
        return iter(self.instructions)

    def __len__(self):
        return self.size

    def __repr__(self):
        return "<Core size=%d width=%d height=%d>" % (self.size, self.width, self.height)

