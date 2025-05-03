# Core War Development Guide

## Project Overview
Core War is a programming game where warriors (programs written in Redcode) battle in a virtual memory arena. This Python implementation provides a MARS (Memory Array Redcode Simulator) that executes these battles.

## Project Structure
```
corewar2d/
├── corewar/          # Core implementation of the MARS simulator
├── warriors/         # Sample warrior programs in Redcode (not needed for code)
├── tests/           # Test suite
├── docs/            # Documentation
├── pixels/          # Graphics-related resources
├── tests.py         # Main test runner
├── README.md        # Project overview
└── dev.md           # Development guide (this file)
```

## Key Components

### MARS (Memory Array Redcode Simulator)
- Located in `corewar/mars.py`
- Core simulation engine that executes warrior programs
- Handles memory management, instruction execution, and process scheduling
- Implements the Redcode instruction set

### Redcode
- Assembly-like programming language for warriors
- Instructions include:
  - DAT (data)
  - MOV (move)
  - ADD/SUB/MUL/DIV/MOD (arithmetic)
  - JMP/JMZ/JMN (jumps)
  - DJN (decrement and jump if not zero)
  - SPL (split process)
  - SLT/CMP/SEQ/SNE (comparisons)
  - NOP (no operation)

### Warrior Programs
- Located in `warriors/`
- Self-replicating programs that compete in the memory arena
- Each warrior has a task queue and process management

## Development Guidelines

### Testing
- Write unit tests for new features
- Run tests using `python -m pytest`
- Maintain test coverage
- Test both successful and error cases

### Documentation
- Update README.md for user-facing changes
- Update dev.md for developer-facing changes
- Keep code comments up to date

## Getting Started

1. Set up virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Unix/macOS
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run tests:
   ```bash
   python -m pytest
   ```

4. Run the simulator:
   ```bash
   python graphics.py warriors/example.red
   ```


## Resources
- [Core War Wikipedia](http://en.wikipedia.org/wiki/Core_War)
- [Redcode Standard](http://www.koth.org/info/icws94.html)
- [Scientific American Articles](https://www.scientificamerican.com/article/core-war/)

# Core War 2D Development Documentation

## 2D Values and Addressing

### Point2D Class
The `Point2D` class represents coordinates in a 2D space. It's designed to be backward compatible with 1D addressing while supporting future 2D memory layouts.

#### Properties
- `x`: The x-coordinate (primary coordinate, used for 1D compatibility)
- `y`: The y-coordinate (currently unused, reserved for future 2D memory)

#### Usage
```python
# 1D usage (backward compatible)
point = Point2D(42)  # y defaults to 0
print(point)  # "42"

# 2D usage
point = Point2D(42, 7)
print(point)  # "42;7"
```

#### Operations
The class supports all basic arithmetic operations with both `Point2D` and integer operands:
- Addition (`+`)
- Subtraction (`-`)
- Multiplication (`*`)
- Division (`/`)
- Modulo (`%`)
- Comparisons (`<`, `>`, `==`)

### Memory Addressing
Currently, the memory is still 1D, but the system is designed to support future 2D memory layouts:

1. **Current Implementation**:
   - Only the x-coordinate is used for memory addressing
   - Addresses wrap around the core size
   - Negative addresses are normalized to positive values

2. **Future 2D Support**:
   - The `point_to_index` method in `MARS` can be modified to use both x and y coordinates
   - Memory layout can be changed without modifying the `Point2D` class
   - All address calculations already use `Point2D`

### Example Usage
```python
# Current 1D addressing
address = Point2D(42)
index = mars.point_to_index(address)  # Returns 42 % core_size

# Future 2D addressing (not yet implemented)
address = Point2D(42, 7)
index = mars.point_to_index(address)  # Could use both x and y for 2D memory layout
```

### Benefits
1. **Backward Compatibility**: Existing 1D code continues to work
2. **Future-Proof**: Ready for 2D memory layouts
3. **Clean Separation**: Address normalization is handled in one place (`point_to_index`)
4. **Flexible**: Memory layout can be changed without modifying the `Point2D` class

### Notes
- The y-coordinate is currently unused but reserved for future 2D memory layouts
- All address calculations should use `Point2D` for future compatibility
- Address normalization (wrapping, negative values) is handled in `point_to_index` 