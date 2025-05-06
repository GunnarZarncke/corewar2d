#! /usr/bin/env python3
# coding: utf-8

from copy import copy
from redcode import Instruction, Point2D

__all__ = ['DEFAULT_INITIAL_INSTRUCTION', 'Core', 'Point2D']

DEFAULT_INITIAL_INSTRUCTION = Instruction('DAT', 'F', None, '$', 0, '$', 0)


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

    def normalize_point(self, point):
        """Normalize a point's coordinates to be within the core's size on each axis. This ensures arithmetic compliant to ICWS"""
        if not isinstance(point, Point2D):
            import traceback
            traceback.print_stack()
            raise ValueError("Point2D expected, got %s" % type(point))
        #if point.x != point.x % self.size or point.y != point.y % self.size:
        #    print(f"normalize_point: {point} -> {Point2D(point.x % self.size, point.y % self.size)}")
        return Point2D(point.x % self.size, point.y % self.size)
            
    def point_to_grid(self, point):
        """Convert a Point2D to 2D grid range, handling 2D wrapping."""
        # For 2D addressing, handle both x and y wrapping
        round_x = point.x // self.width    # how many times you wrapped in x
        x_new  = point.x % self.width

        raw_y = point.y + round_x
        round_y = point.y // self.height # how many times you wrapped in y
        final_y = raw_y % self.height

        final_x = (x_new + round_y) % self.width
        #print(f"point_to_grid: {point} -> {Point2D(final_x, final_y)}")
        return Point2D(final_x, final_y)

    def point_to_index(self, point):
        if not isinstance(point, Point2D):
            import traceback
            traceback.print_stack()
            raise ValueError("Point2D expected, got %s" % type(point))
            
        ongrid = self.point_to_grid(point)
        return ongrid.y * self.width + ongrid.x

    def trim(self, value):
        "Return a trimmed value to the bounds of the core size"
        return self.normalize_point(value)
    
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
        #print(f"set: {address} [{self.point_to_index(address)}] = {instruction}")
        self.instructions[self.point_to_index(address)] = instruction

    def __iter__(self):
        return iter(self.instructions)

    def __len__(self):
        return self.size

    def __repr__(self):
        return "<Core size=%d width=%d height=%d>" % (self.size, self.width, self.height)

