#!/usr/bin/env python3
# coding: utf-8

import sys
import os
import re
import readline
import atexit

from redcode import parse, Point2D, Warrior
from mars import MARS, EVENT_EXECUTED, EVENT_I_WRITE, EVENT_I_READ, EVENT_A_DEC, EVENT_A_INC, EVENT_B_DEC, EVENT_B_INC, EVENT_A_READ, EVENT_A_WRITE, EVENT_B_READ, EVENT_B_WRITE, EVENT_A_ARITH, EVENT_B_ARITH, STEP_NORMAL, STEP_VERTICAL, STEP_BACKWARD, STEP_VERTICAL_BACKWARD
from core import DEFAULT_INITIAL_INSTRUCTION

# Set up history file
HISTORY_FILE = os.path.expanduser('~/.mars_repl_history')

def setup_history():
    """Set up readline history file."""
    try:
        readline.read_history_file(HISTORY_FILE)
        # Set history file size
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass
    
    # Register history file saving on exit
    atexit.register(readline.write_history_file, HISTORY_FILE)

class MARSREPL(MARS):
    """A MARS with REPL capabilities for interactive execution and debugging."""
    
    def __init__(self, *args, **kwargs):
        super(MARSREPL, self).__init__(*args, **kwargs)
        # Automatically create event names by removing 'EVENT_' prefix
        self.event_names = {
            event_type: name.replace('EVENT_', '')
            for name, event_type in globals().items()
            if name.startswith('EVENT_')
        }
        # Create a single event handler for all events
        self.event_handlers = {
            event_type: lambda w, p, e=event_type: self._handle_event(e, p)
            for event_type in self.event_names.keys()
        }
    
    def _handle_event(self, event_type, address):
        """Handle all events with consistent formatting."""
        event_name = self.event_names[event_type]
        instruction = self.get_instruction(address)
        print(f"{str(address).ljust(9)} {str(instruction).ljust(30)} ; {event_name}")
    
    def core_event(self, warrior, address, event_type):
        """Handle core events by calling the appropriate event handler."""
        if event_type in self.event_handlers:
            self.event_handlers[event_type](warrior, address)

def parse_point2d(point_str):
    """Parse a Point2D string, accepting either a single number or x:y format."""
    return Point2D(point_str, 0)

def handle_step_command(mars, warrior):
    """Handle the step command."""
    if not warrior.task_queue:
        print("Process terminated")
        return
    mars.step()
    if warrior.task_queue:
        if len(warrior.task_queue) > 1:
            print(f"Next positions: {warrior.task_queue}")
    else:
        print("Process terminated")

def handle_set_pc_command(line, warrior):
    """Handle the set PC command."""
    try:
        point_str = line[1:].strip()
        point = parse_point2d(point_str)
        if point is not None:
            warrior.task_queue = [point]
            print(f"Program counter set to {point}")
        else:
            print("Invalid point format. Use a number (e.g. '=5') or x:y format (e.g. '=1:2')")
    except Exception as e:
        print(f"Error setting PC: {str(e)}")

def handle_clear_command(mars, warrior):
    """Handle the clear command."""
    mars.reset()
    warrior.task_queue = [Point2D(0, 0)]
    print("Memory cleared")

def handle_save_command(line, mars, warrior):
    """Handle the save command."""
    try:
        filename = line[5:].strip()
        if not filename:
            print("Please specify a filename")
            return
        
        # Start at position 0,0 and follow the program path
        visited = set()
        instructions = []
        pos = Point2D(0, 0)
        
        while True:
            instr = mars.get_instruction(pos)
            if instr == DEFAULT_INITIAL_INSTRUCTION:
                break
                
            # If we've seen this position before, we've completed a cycle
            if pos in visited:
                # Find where the cycle starts
                cycle_start = instructions.index((pos, instr))
                # Add a comment to mark the cycle
                instructions.append((pos, instr))
                instructions.append((None, "; Cycle detected - program repeats from here"))
                break
                
            instructions.append((pos, instr))
            visited.add(pos)
            
            # Follow the stepping mode to get next position
            if instr.stepping == STEP_NORMAL:
                pos = Point2D(pos.x + 1, pos.y)
            elif instr.stepping == STEP_VERTICAL:
                pos = Point2D(pos.x, pos.y + 1)
            elif instr.stepping == STEP_BACKWARD:
                pos = Point2D(pos.x - 1, pos.y)
            elif instr.stepping == STEP_VERTICAL_BACKWARD:
                pos = Point2D(pos.x, pos.y - 1)
        
        if not instructions:
            print("No instructions to save")
            return
        
        # Save instructions to file
        with open(filename, 'w') as f:
            f.write(f"; Saved from MARS REPL\n")
            f.write(f"; Author: {warrior.author}\n")
            f.write(f"; Name: {warrior.name}\n\n")
            
            # Write instructions in order of execution
            for pos, instr in instructions:
                if pos is None:
                    # This is a comment line
                    f.write(f"{instr}\n")
                else:
                    f.write(f"{instr}\n")
        
        print(f"Program saved to {filename}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")

def handle_memory_inspection(line, mars):
    """Handle memory inspection command."""
    point_str = line[1:].strip()
    point = parse_point2d(point_str)
    if point is not None:
        instruction = mars.get_instruction(point)
        print(f"{str(point).ljust(9)} {str(instruction).ljust(30)} ; MEMORY")
        print(f"Memory at {point}: {instruction}")
    else:
        print("Invalid point format. Use a number (e.g. '?5') or x:y format (e.g. '?1:2')")

def handle_instruction(line, mars, warrior):
    """Handle Redcode instruction execution."""
    try:
        # Parse the instruction
        parsed_warrior = parse([line])
        if not parsed_warrior or not parsed_warrior.instructions:
            print("No valid instruction found")
            return
        
        # Get the instruction from the parsed warrior
        instruction = next(iter(parsed_warrior.instructions.values()))
        
        # If warrior's task queue is empty, reset it to the current position
        if not warrior.task_queue:
            warrior.task_queue = [Point2D(0, 0)]
        
        # Place the instruction at the current position
        current_pos = warrior.task_queue[0]
        mars.set_instruction(current_pos, instruction)
        
        # Execute the instruction
        mars.step()
        
        # Show the next position
        if warrior.task_queue:
            if len(warrior.task_queue) > 1:
                print(f"Next positions: {warrior.task_queue}")
        else:
            print("Process terminated")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def print_help():
    """Print the help message."""
    print("MARS REPL - Interactive Redcode Execution Environment")
    print("Enter Redcode instructions or '?x:y' to view memory contents")
    print("Commands:")
    print("  clear    - Reset memory")
    print("  save <f> - Save current program to file")
    print("  ?<pc>    - Show memory at <pc>")
    print("  =<pc>    - Set program counter (e.g. '=5' or '=1:2')")
    print("  step     - Execute one step")
    print("  quit     - Exit REPL")
    print("Use up/down arrows to navigate command history")
    print()

def main():
    # Set up command history
    setup_history()
    
    # Create a MARS instance with REPL capabilities
    mars = MARSREPL()
    
    # Create a default warrior for executing instructions
    warrior = Warrior()
    warrior.name = "REPL"
    warrior.author = "REPL"
    warrior.task_queue = [Point2D(0, 0)]
    mars.warriors = [warrior]
    
    print_help()
    
    while True:
        try:
            # Get user input
            current_pc = warrior.task_queue[0] if warrior.task_queue else "terminated"
            line = input(f"MARS [{current_pc}]> ").strip()
            
            # Handle exit commands
            if line.lower() in ('quit', 'exit'):
                break
            
            # Handle step command
            if line.lower() == 'step':
                handle_step_command(mars, warrior)
                continue
            
            # Handle set PC command
            if line.startswith('='):
                handle_set_pc_command(line, warrior)
                continue
            
            # Handle clear command
            if line.lower() == 'clear':
                handle_clear_command(mars, warrior)
                continue
            
            # Handle save command
            if line.lower().startswith('save '):
                handle_save_command(line, mars, warrior)
                continue
            
            # Handle memory inspection
            if line.startswith('?'):
                handle_memory_inspection(line, mars)
                continue
            
            # Handle Redcode instruction
            handle_instruction(line, mars, warrior)
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except EOFError:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main() 