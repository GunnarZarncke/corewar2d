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