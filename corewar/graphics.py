#! /usr/bin/env python3
# coding: utf-8

import os
import sys
import pygame
from pygame.locals import *

from core import DEFAULT_INITIAL_INSTRUCTION
from mars import MARS, EVENT_EXECUTED, EVENT_I_WRITE, EVENT_I_READ, EVENT_A_DEC, EVENT_A_INC, EVENT_B_DEC, EVENT_B_INC, EVENT_A_READ, EVENT_A_WRITE, EVENT_B_READ, EVENT_B_WRITE, EVENT_A_ARITH, EVENT_B_ARITH
from redcode import Point2D,parse, Warrior, DAT, MOV, ADD, SUB, MUL, DIV, MOD, JMP, JMZ, JMN, DJN, SPL, SLT, CMP, SEQ, SNE, NOP

INSTRUCTIONS_PER_LINE = 100
INSTRUCTION_SIZE_X = 9
INSTRUCTION_SIZE_Y = 9

ZOOM_VIEW_WIDTH = 200

I_SIZE = (INSTRUCTION_SIZE_X, INSTRUCTION_SIZE_Y)
I_AREA = ((0,0), I_SIZE)

IMAGE_BG_COLOR = (255,255,254,255)
IMAGE_FG_COLOR = (0,0,1,255)

OPCODE_SURFACES = None

DEFAULT_BG_COLOR = (0, 0, 0)
DEFAULT_FG_COLOR = (60,60,60)
BLACK = (0, 0, 0)
WHITE = (255,255,255)

# Colors are dark and bright
WARRIOR_COLORS = (((0,0,100), (0,0,255)),
                  ((0,100,0), (0,255,0)),
                  ((0,100,100), (0,255,255)),
                  ((100,0,0), (255,0,0)),
                  ((100,0,100), (255,0,255)),
                  ((100,100,0), (255,255,0)))

def load_opcode_surfaces():
    "Load the images of the opcodes from the file"
    all_instructions = pygame.image.load('pixels/instructions.png')
    class Y:
        y = -INSTRUCTION_SIZE_Y
        def __call__(self):
            self.y += INSTRUCTION_SIZE_Y
            return self.y
    y = Y()

    return {
        DAT: all_instructions.subsurface(((0,y()), I_SIZE)),
        MOV: all_instructions.subsurface(((0,y()), I_SIZE)),
        ADD: all_instructions.subsurface(((0,y()), I_SIZE)),
        SUB: all_instructions.subsurface(((0,y()), I_SIZE)),
        MUL: all_instructions.subsurface(((0,y()), I_SIZE)),
        DIV: all_instructions.subsurface(((0,y()), I_SIZE)),
        MOD: all_instructions.subsurface(((0,y()), I_SIZE)),
        JMP: all_instructions.subsurface(((0,y()), I_SIZE)),
        JMZ: all_instructions.subsurface(((0,y()), I_SIZE)),
        JMN: all_instructions.subsurface(((0,y()), I_SIZE)),
        DJN: all_instructions.subsurface(((0,y()), I_SIZE)),
        SPL: all_instructions.subsurface(((0,y()), I_SIZE)),
        SLT: all_instructions.subsurface(((0,y()), I_SIZE)),
        CMP: all_instructions.subsurface(((0,y()), I_SIZE)),
        SEQ: all_instructions.subsurface(((0,y()), I_SIZE)),
        SNE: all_instructions.subsurface(((0,y()), I_SIZE)),
        NOP: all_instructions.subsurface(((0,y()), I_SIZE))}

def opcode_surface(opcode, foreground=None, background=None):
    "Return a surface representing an instruction in the core"
    surface = pygame.Surface(I_SIZE)
    opcode_surface = OPCODE_SURFACES[opcode].convert(surface)

    if background:
        surface.fill(background) # fill background color
        opcode_surface.set_colorkey(IMAGE_BG_COLOR) # make image bg transparent
        surface.blit(opcode_surface, (0,0)) # blit opcode in background
        surface.set_colorkey(IMAGE_FG_COLOR) # make image fg transparent

    if foreground:
        fg_surface = pygame.Surface(I_SIZE)
        fg_surface.fill(foreground) # fill foreground color
        opcode_surface.set_colorkey(IMAGE_FG_COLOR) # make image fg transparent
        fg_surface.blit(opcode_surface, (0,0)) # blit opcode in background
        fg_surface.set_colorkey(IMAGE_BG_COLOR) # make image bg transparent

        surface.blit(fg_surface, (0,0)) # blit in background

    return surface

class PygameMARS(MARS):
    "A MARS with a surface drawing of the core"

    def __init__(self, *args, **kargs):
        super(PygameMARS, self).__init__(*args, **kargs)
        self.size = (INSTRUCTION_SIZE_X * INSTRUCTIONS_PER_LINE,
                     INSTRUCTION_SIZE_Y * (len(self) / INSTRUCTIONS_PER_LINE))
        self.core_surface = pygame.Surface(self.size)
        self.recent_events = pygame.Surface(self.size)
        self.recent_events.set_colorkey(DEFAULT_BG_COLOR)
        self.energy_surface = pygame.Surface(self.size)
        self.energy_surface.set_colorkey(DEFAULT_BG_COLOR)

    def reset(self, clear_instruction=DEFAULT_INITIAL_INSTRUCTION):
        self.core.clear(clear_instruction)
        for n, instruction in enumerate(self):
            self.core_surface.blit(opcode_surface(instruction.opcode,
                                                  DEFAULT_FG_COLOR,
                                                  DEFAULT_BG_COLOR),
                                   ((n % INSTRUCTIONS_PER_LINE) * INSTRUCTION_SIZE_X,
                                    (n / INSTRUCTIONS_PER_LINE) * INSTRUCTION_SIZE_Y))
        self.load_warriors()
        self.update_energy_display()

    def load_warriors(self):
        super(PygameMARS, self).load_warriors()
        for instruction in self:
            instruction.fg_color = DEFAULT_FG_COLOR
            instruction.bg_color = DEFAULT_BG_COLOR
        self.update_energy_display()

    def step(self):
        self.recent_events.fill(DEFAULT_BG_COLOR)
        super(PygameMARS, self).step()
        if self.energy_mode:
            self.update_energy_display()

    def update_energy_display(self):
        """Update the energy visualization surface."""
        self.energy_surface.fill(DEFAULT_BG_COLOR)
        for n, instruction in enumerate(self):
            if self.energy_mode and instruction.energy > 0:
                # Calculate energy bar height (0-100%)
                energy_height = int((instruction.energy / 1000.0) * INSTRUCTION_SIZE_Y)
                if energy_height > 0:
                    # Draw energy bar
                    energy_rect = pygame.Rect(
                        (n % INSTRUCTIONS_PER_LINE) * INSTRUCTION_SIZE_X,
                        (n / INSTRUCTIONS_PER_LINE) * INSTRUCTION_SIZE_Y + (INSTRUCTION_SIZE_Y - energy_height),
                        INSTRUCTION_SIZE_X,
                        energy_height
                    )
                    # Use a gradient from green to red based on energy level
                    energy_color = (
                        int(255 * (1 - instruction.energy / 1000.0)),  # Red component
                        int(255 * (instruction.energy / 1000.0)),      # Green component
                        0                                             # Blue component
                    )
                    pygame.draw.rect(self.energy_surface, energy_color, energy_rect)

    def blit_into(self, surface, dest):
        surface.blit(self.core_surface, dest)
        if self.energy_mode:
            surface.blit(self.energy_surface, dest)
        surface.blit(self.recent_events, dest)

    def core_event(self, warrior, address, event_type):
        if not isinstance(address, Point2D):
            raise ValueError("address must be a Point2D")
            
        # Ensure address is within bounds
        address = self.core.point_to_grid(address)
        
        # Calculate position for drawing
        position = ((address.x % INSTRUCTIONS_PER_LINE) * INSTRUCTION_SIZE_X,
                    (address.y % (self.core.size // INSTRUCTIONS_PER_LINE)) * INSTRUCTION_SIZE_Y)
        
        instruction = self.core[address]

        if event_type in (EVENT_I_WRITE, EVENT_A_WRITE, EVENT_B_WRITE):
            # In case of a write event, we write the foreground with the
            # warrior's color
            self.core_surface.blit(opcode_surface(instruction.opcode,
                                                  warrior.color[1],
                                                  None),
                                   position, area=I_AREA)
            self.recent_events.blit(opcode_surface(instruction.opcode,
                                                   WHITE,
                                                   DEFAULT_BG_COLOR),
                                    position, area=I_AREA)
            instruction.fg_color = warrior.color[1]
        elif event_type == EVENT_EXECUTED:
            # In case of execution, we write the background with warrior's color
            self.core_surface.blit(opcode_surface(instruction.opcode,
                                                  WHITE,
                                                  warrior.color[0]),
                                   position, area=I_AREA)
            self.recent_events.blit(opcode_surface(instruction.opcode,
                                                   BLACK,
                                                   warrior.color[1]),
                                    position, area=I_AREA)
            instruction.fg_color = WHITE
            instruction.bg_color = warrior.color[0]
        elif event_type in (EVENT_A_ARITH, EVENT_B_ARITH, EVENT_A_DEC,
                            EVENT_B_DEC, EVENT_A_INC, EVENT_B_INC):
            # In case of arithmetic modification, or increment/decrement, we
            # write a rectangle around the instruction
            pygame.draw.rect(self.core_surface, warrior.color[0],
                             (position, (INSTRUCTION_SIZE_X, INSTRUCTION_SIZE_Y)),
                              1)
            pygame.draw.rect(self.recent_events, warrior.color[1],
                             (position, (INSTRUCTION_SIZE_X, INSTRUCTION_SIZE_Y)),
                              1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='MARS (Memory Array Redcode Simulator)')
    parser.add_argument('--rounds', '-r', metavar='ROUNDS', type=int, nargs='?',
                        default=1, help='Rounds to play')
    parser.add_argument('--paused', action='store_true', default=False,
                        help='Start each round paused')
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
    parser.add_argument('warriors', metavar='WARRIOR', type=argparse.FileType('r'), nargs='+',
                        help='Warrior redcode filename')

    args = parser.parse_args()

    if len(args.warriors) > len(WARRIOR_COLORS):
        print("Please specify a maximum of %d warriors." % len(WARRIOR_COLORS), file=sys.stderr)
        sys.exit(1)

    # build environment
    environment = {'CORESIZE': args.size,
                   'CYCLES': args.cycles,
                   'ROUNDS': args.rounds,
                   'MAXPROCESSES': args.processes,
                   'MAXLENGTH': args.length,
                   'MINDISTANCE': args.distance}

    # assemble warriors
    warriors = [parse(file, environment) for file in args.warriors]

    # initialize wins, losses, ties and color for each warrior
    for warrior, color in zip(warriors, WARRIOR_COLORS):
        warrior.wins = warrior.ties = warrior.losses = 0
        warrior.color = color

    # create MARS
    simulation = PygameMARS(minimum_separation = args.distance,
                            max_processes = args.processes,
                            total_energy = args.energy)
    simulation.warriors = warriors

    # initialize pygame engine
    pygame.init()

    # core instruction's font
    core_font = pygame.font.SysFont("monospace", 12)

    # Load surfaces from file
    OPCODE_SURFACES = load_opcode_surfaces()

    # create display
    display_surface = pygame.display.set_mode((simulation.size[0] + ZOOM_VIEW_WIDTH,
                                               simulation.size[1]))

    # initializations
    c_address = 0

    # control variables
    paused = False
    stop_rounds = False

    # create clock to control FPS
    clock = pygame.time.Clock()

    # for each round
    for round in range(1, args.rounds + 1):
        # reset simulation and load warriors
        simulation.reset()

        # start with all warriors active
        active_warriors = list(warriors)

        # how many warriors should be playing to skip to next round
        active_warrior_to_stop = 1 if len(warriors) >= 2 else 0

        # start paused if user requested from command line
        if args.paused:
            paused = True

        # control variable
        next_round = False

        print()
        print("Starting round %d" % round)

        for cycle in range(args.cycles):
            # step one simulation in MARS
            simulation.step()

            # get mouse position
            mouse_pos = pygame.mouse.get_pos()
            # calculate address based on mouse position if position is over core
            if 0 <= mouse_pos[0] <= simulation.size[0] and 0 <= mouse_pos[1] <= simulation.size[1]:
                c_address = (INSTRUCTIONS_PER_LINE * (mouse_pos[1]//INSTRUCTION_SIZE_Y) +
                             (mouse_pos[0] // INSTRUCTION_SIZE_X))

            # clear display part of instructions
            display_surface.fill(BLACK, ((simulation.size[0], 0),
                                         (ZOOM_VIEW_WIDTH, simulation.size[1])))
            for n, address in enumerate(range(c_address-18, c_address+18)):
                instruction = simulation[Point2D(address,0)]
                i_surface = core_font.render("%04d %s" % (address,
                                                          instruction),
                                               True,
                                               instruction.fg_color)
                pygame.draw.rect(display_surface, instruction.bg_color,
                                 ((simulation.size[0], n*20),
                                  (simulation.size[0] + ZOOM_VIEW_WIDTH,
                                   (n+1)*20)))
                display_surface.blit(i_surface, (simulation.size[0], n*20))

            # blit MARS visualization into display
            simulation.blit_into(display_surface, (0,0))
            pygame.display.update()
            clock.tick(30)

            to_remove = []
            for warrior in active_warriors:
                if not warrior.task_queue:
                    energy_info = " (energy mode)" if simulation.energy_mode else ""
                    print("%s (%s) losses after %d cycles%s." % (warrior.name,
                                                               warrior.author,
                                                               cycle,
                                                               energy_info))
                    warrior.losses += 1
                    to_remove.append(warrior)

            for warrior in to_remove:
                active_warriors.remove(warrior)

            # if there's only one left, or are all dead, then stop simulation
            if len(active_warriors) <= active_warrior_to_stop:
                for warrior in active_warriors:
                    energy_info = " (energy mode)" if simulation.energy_mode else ""
                    print("%s (%s) wins after %d cycles%s." % (warrior.name,
                                                             warrior.author,
                                                             cycle,
                                                             energy_info))
                    warrior.wins += 1
                break

            step = False
            while True:
                for event in pygame.event.get():
                    #print("Event:"+str(event))
                    if event.type == QUIT:
                        # Tie all remaining bots and go to final results
                        next_round = True
                        stop_rounds = True
                        paused = False
                    elif event.type == KEYDOWN:
                        if event.key == K_SPACE:
                            # toggle pausing
                            paused = not paused
                        elif event.key == K_s:
                            # step simulation (and pause)
                            paused = True
                            step = True
                        elif event.key == K_n:
                            # Tie all remaining bots and go to next round
                            next_round = True

                if not paused or step or next_round:
                    break

            if next_round:
                for warrior in active_warriors:
                    if warrior.task_queue:
                        energy_info = " (energy mode)" if simulation.energy_mode else ""
                        print("%s (%s) ties after %d cycles%s." % (warrior.name,
                                                                 warrior.author,
                                                                 cycle,
                                                                 energy_info))
                        warrior.ties += 1
                break
        else:
            # running until max cycles: tie
            for warrior in active_warriors:
                if warrior.task_queue:
                    energy_info = " (energy mode)" if simulation.energy_mode else ""
                    print("%s (%s) ties after %d cycles%s." % (warrior.name,
                                                             warrior.author,
                                                             cycle,
                                                             energy_info))
                    warrior.ties += 1

        if stop_rounds:
            break

    # print final results
    print()
    print("Final results: (%d rounds)" % round)
    print("%s %s %s %s" % ("Warrior (Author)".ljust(40), "wins".rjust(5),
                           "ties".rjust(5), "losses".rjust(5)))
    for warrior in warriors:
        print("%s %s %s %s" % (("%s (%s)" % (warrior.name, warrior.author)).ljust(40),
                               str(warrior.wins).rjust(5),
                               str(warrior.ties).rjust(5),
                               str(warrior.losses).rjust(5)))

    if not stop_rounds and not next_round:
        # keeps display open, until quit
        paused = True
        while paused:
            for event in pygame.event.get():
                if event.type == QUIT:
                    paused = False

    # exit pygame
    pygame.quit()

