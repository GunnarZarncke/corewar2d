# Core War

[![Build Status](https://travis-ci.org/rodrigosetti/corewar.svg?branch=master)](https://travis-ci.org/rodrigosetti/corewar)

The Canadian mathematician A. K. Dewdney (author of "The Planiverse") first
introduced Core War in a series of Scientific American articles
starting in 1984.

> Core War was inspired by a story I heard some years ago about a mischievous
> programmer at a large corporate research laboratory I shall designate X. The
> programmer wrote an assembly-language program called Creeper that would
> duplicate itself every time it was run. It could also spread from one
> computer to another in the network of the X corporation. The program had no
> function other than to perpetuate itself. Before long there were so many
> copies of Creeper that more useful programs and data were being crowded out.
> The growing infestation was not brought under control until someone thought
> of fighting fire with fire. A second self-duplicating program called Reaper
> was written.  Its purpose was to destroy copies of Creeper until it could
> find no more and then to destroy itself. Reaper did its job, and things were
> soon back to normal at the X lab.

In this game, computer programs (called "Warriors") compete in a virtual arena
for digital supremacy. Warriors are written in an Assembly dialect called
"Redcode".

[Wikipedia article](http://en.wikipedia.org/wiki/Core_War)

This is a Python implementation of the MARS (Memory Array Redcode Simulator).

## Core War 2D

This project extends Core War into two dimensions, allowing for more complex and interesting warrior programs. The 2D implementation includes:

- 2D memory addressing with Point2D coordinates
- Vertical and diagonal movement
- Enhanced stepping modes
- Interactive REPL for program development

### MARS REPL

The MARS REPL (Memory Array Redcode Simulator Read-Eval-Print Loop) is an interactive environment for writing and testing Redcode programs.

#### Features

- Interactive execution of Redcode instructions
- Real-time memory inspection
- Program counter control
- Command history with up/down arrow navigation
- Program saving with cycle detection
- Step-by-step execution
- Event display for debugging

#### Usage

Start the REPL:
```bash
python -m corewar.mars_repl
```

#### Commands

- `clear` - Reset memory
- `save <file>` - Save current program to file
- `?<pc>` - Show memory at position (e.g. `?5` or `?1:2`)
- `=<pc>` - Set program counter (e.g. `=5` or `=1:2`)
- `step` - Execute one step
- `quit` - Exit REPL

#### Example Session

```
MARS [(0,0)]> MOV.I #0, 0
Next positions: [(1,0)]
MARS [(1,0)]> ?0
(0,0)     MOV.I    # 0, $ 0          ; MEMORY
MARS [(1,0)]> step
Next positions: [(2,0)]
MARS [(2,0)]> save my_program.red
Program saved to my_program.red
```

### Redcode Instructions

The simulator supports all standard Redcode instructions:
- DAT - Data (kills process)
- MOV - Move
- ADD - Add
- SUB - Subtract
- MUL - Multiply
- DIV - Divide
- MOD - Modulo
- JMP - Jump
- JMZ - Jump if Zero
- JMN - Jump if Not Zero
- DJN - Decrement and Jump if Not Zero
- SPL - Split
- SLT - Skip if Less Than
- CMP/SEQ - Compare/Skip if Equal
- SNE - Skip if Not Equal
- NOP - No Operation

Each instruction can be modified with:
- Addressing modes: # (immediate), $ (direct), @ (indirect), < (pre-decrement), > (post-increment)
- Modifiers: .A, .B, .AB, .BA, .F, .X, .I
- Stepping modes: .D (normal), .S (vertical), .Q (backward), .W (vertical backward)

### Running the Simulator

    usage: graphics.py [-h] [--rounds [ROUNDS]] [--paused] [--size [CORESIZE]]
                       [--cycles [CYCLES]] [--processes [MAXPROCESSES]]
                       [--length [MAXLENGTH]] [--distance [MINDISTANCE]]
                       WARRIOR [WARRIOR ...]

    MARS (Memory Array Redcode Simulator)

    positional arguments:
      WARRIOR               Warrior redcode filename

    optional arguments:
      -h, --help            show this help message and exit
      --rounds [ROUNDS], -r [ROUNDS]
                            Rounds to play
      --paused              Start each round paused
      --size [CORESIZE], -s [CORESIZE]
                            The core size
      --cycles [CYCLES], -c [CYCLES]
                            Cycles until tie
      --processes [MAXPROCESSES], -p [MAXPROCESSES]
                            Max processes
      --length [MAXLENGTH], -l [MAXLENGTH]
                            Max warrior length
      --distance [MINDISTANCE], -d [MINDISTANCE]
                            Minimum warrior distance
