#!/usr/bin/env python

"""
Simple python implementation of Conway's Game of Life

Author: Terry Dolan

Date: April 2015

Acknowledgements:
John Conway
http://en.wikipedia.org/wiki/Conway%27s_Game_of_Life
http://www.conwaylife.com/wiki
Al Sweigart, http://inventwithpython.com/pygame/
Richard Jones, PyCon pygame tutorial
"""

import random, pygame, sys
from pygame.locals import *
from collections import defaultdict

FPS = 10 # frames per second
WINDOW_TITLE = 'Game of Life'
WINDOW_WIDTH = 1020
WINDOW_HEIGHT = 560
CELL_SIZE = 10
assert WINDOW_WIDTH % CELL_SIZE == 0, "Window width must be a multiple of cell size."
assert WINDOW_HEIGHT % CELL_SIZE == 0, "Window height must be a multiple of cell size."
CELL_WIDTH = int(WINDOW_WIDTH / CELL_SIZE)
CELL_HEIGHT = int(WINDOW_HEIGHT / CELL_SIZE)
START_FRACTION = 8 # 1/START_FRACTION of cells in grid is generated randomly at start
CENTRE_CELL = (int(CELL_WIDTH/2), int(CELL_HEIGHT/2))

# some interesting pattern files
# these can be loaded as part of the grid initialisation
GOSPER_GLIDER_GUN = 'gosperglidergun_106.lif' 
ACORN = 'acorn_106.lif' 
SWITCH_ENGINE = 'switchengine_106.lif'
GLIDER = 'glider_106.lif'
RPENTOMINO = 'rpentomino_106.lif'
DIEHARD = 'diehard_106.lif'

#             R    G    B
WHITE     = (255, 255, 255)
BLACK     = (  0,   0,   0)
RED       = (255,   0,   0)
GREEN     = (  0, 255,   0)
DARK_GREEN = (  0, 155,   0)
DARK_GREY  = ( 40,  40,  40)
BG_COLOUR = BLACK # colour of background (and dead cells)
LIVECELL_COLOUR = RED # colour of live cells


def initialise_grid():
    """Return cells set to initial conditions.

        Type r to create random set of cells.
        Type g to load gosper glider gun pattern.
        Type a to load acorn pattern.
        Type s to load switch engine pattern.
        Type l to load glider pattern.
        Type p to load rpentomino pattern.
        Type d to load diehard pattern.
                
        Or use mouse click to toggle cell.
        Type RETURN when complete.

        Output: dictionary of cell co-ordinates with boolean value
        - True indicates cell is alive
        - False indicates cell is dead
    """

    # set initialisation window title with hint
    INIT_HINT = ' (set initial conditions [mouse|r|g|a|s|l|p|d] and press RETURN to start; or ESC to quit)'
    pygame.display.set_caption(WINDOW_TITLE + INIT_HINT)
    
    # create dictionary of empty (dead) cells
    cells = initialise_empty_cells()
    
    is_grid_set = False
    while not is_grid_set: # loop to initialise grid
        for event in pygame.event.get(): 
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()
                elif event.key == K_RETURN:
                    is_grid_set = True
                    break
                elif event.key == K_r:
                    # r key pressed, generate random set of cells
                    cells = initialise_random_cells(START_FRACTION)
                elif event.key == K_g:
                    # load Gosper glider gun
                    cells = life_load((20, 6), GOSPER_GLIDER_GUN)
                elif event.key == K_a:
                    # load Acorn
                    cells = life_load(CENTRE_CELL, ACORN)
                elif event.key == K_s:
                    # load Switch Engine
                    cells = life_load(CENTRE_CELL, SWITCH_ENGINE)
                elif event.key == K_l:
                    # load Glider
                    cells = life_load((3, 3), GLIDER)
                elif event.key == K_p:
                    # load Rpentomino
                    cells = life_load(CENTRE_CELL, RPENTOMINO)
                elif event.key == K_d:
                    # load Diehard
                    cells = life_load(CENTRE_CELL, DIEHARD)
            elif event.type == MOUSEBUTTONUP:
                # find cell selected using mouse and toggle
                mx, my = pygame.mouse.get_pos()
                this_cell = (int(mx // CELL_SIZE), int(my // CELL_SIZE))
                cells[this_cell] = not cells[this_cell]    

        DISPLAY_SURFACE.fill(BG_COLOUR)
        draw_grid_lines() # draw grid
        draw_cells(cells) # draw cells initialised so far
        pygame.display.update()
        FPS_CLOCK.tick(FPS)

    return cells


def life_load(centre_cell, filename):
    """Load filename containing life centred at given centre_cell

       File should be in Life 1.06 format
       Ref: http://www.conwaylife.com/wiki/Life_1.06

       Output: initialised cells
    """
    cx, cy = centre_cell
    cells = initialise_empty_cells()

    with open(filename, 'r') as f:
        for line in f:
            if line[0] != '#': # ignore comments
                x, y = map(int, line.split())
                # bring cell to life, centred on centre cell
                livecell = (cx + x, cy + y)
                cells[livecell] = True 

    return cells


def live_or_die(cells):
    """Apply Conway's Game of Life rules to this generation of cells.

    Rules:
    1. Any live cell with fewer than two live neighbours dies, as if caused by under-population.
    2. Any live cell with two or three live neighbours lives on to the next generation.
    3. Any live cell with more than three live neighbours dies, as if by overcrowding.
    4. Any dead cell with exactly three live neighbours becomes a live cell, as if by reproduction.

    Input: dictionary of cell co-ordinates with boolean True indicating alive e.g. cells[(1,2)] = True
    Output: updated dictionary with rules applied 
    """
    
    # create next gen of cells, starting with copy of current gen
    cells_ngen = cells.copy()
    
    # create dictionary of live cells with neighbour count value initialised to zero
    livecells = {(x, y): 0 for (x, y), alive in cells.items() if alive}

    # create dictionary to hold dead cells near live cells that may be resurrected
    deadcell_candidates = defaultdict(int)
    
    # calculate neighbour count for livecells
    for this_livecell in livecells:
        for this_livecell_neighbour in cell_neighbours(this_livecell):
            if this_livecell_neighbour in livecells:
                # neighbour is alive
                livecells[this_livecell] += 1
            else:
                # neighbour is dead and becomes candidate for resurrection
                deadcell_candidates[this_livecell_neighbour] += 1
                
    # determine who lives and who dies by checking the neighbour count
    for this_cell, neighbour_count in livecells.iteritems():
        if neighbour_count < 2: # rule 1, kill cell
            cells_ngen[this_cell] = False 
        elif 2 <= neighbour_count <= 3: # rule 2, cell continues to live
            pass  
        elif neighbour_count > 3: # rule 3, kill cell
            cells_ngen[this_cell] = False 

    # determine which deadcell candidate reproduces by checking neighbour count    
    for this_cell, neighbour_count in deadcell_candidates.iteritems():
        if neighbour_count == 3: # rule 4, bring cell to life
            # apply simple boundary condition
            # - life is extinguished beyond the display surface
            if is_in_display_surface(this_cell): 
                cells_ngen[this_cell] = True

    return cells_ngen


def is_in_display_surface(cell):
    """Return True if given cell is in display surface."""
    x, y = cell
    return all([x >= 0, x < CELL_WIDTH, y >= 0, y < CELL_HEIGHT])

def terminate():
    """Terminate program."""
    pygame.quit()
    sys.exit()


def draw_grid_lines():
    """Draw the grid lines."""
    for x in range(0, WINDOW_WIDTH, CELL_SIZE): # draw vertical lines
        pygame.draw.line(DISPLAY_SURFACE, DARK_GREY, (x, 0), (x, WINDOW_HEIGHT))
    for y in range(0, WINDOW_HEIGHT, CELL_SIZE): # draw horizontal lines
        pygame.draw.line(DISPLAY_SURFACE, DARK_GREY, (0, y), (WINDOW_WIDTH, y))


def gen_cell_random(n):
    """Yield n unique random cells in the grid."""
    s = set()
    for _ in range(n):
        while True:
            randomcell = (random.randint(0, CELL_WIDTH-1), random.randint(0, CELL_HEIGHT-1))
            if randomcell not in s:
                s.add(randomcell)
                yield randomcell
                break


def initialise_random_cells(n):
    """Initialise random set of cells using 1/n th of the grid."""
    cells = initialise_empty_cells()
    for x, y in gen_cell_random(int(CELL_WIDTH*CELL_HEIGHT/n)):
        cells[(x, y)] = True
        
    return cells


def initialise_empty_cells():
    """Initialise empty dictionary of cells for the grid."""
    cells = {(x, y): False for x in range(CELL_WIDTH) for y in range(CELL_HEIGHT)}
    return cells

        
def draw_cells(cells):
    """Draw all live cells."""
    livecells = (livecell for livecell, alive in cells.items() if alive)
    for (x,y) in livecells:
        pygame.draw.rect(DISPLAY_SURFACE, LIVECELL_COLOUR,
                         (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))     


def cell_neighbours((x,y)):
    """Return neighbours of given cell."""
    return [(x-1, y-1), (x, y-1), (x+1, y-1), 
            (x-1, y), (x+1, y), 
            (x-1, y+1), (x, y+1), (x+1, y+1),]


def main():
    global FPS_CLOCK, DISPLAY_SURFACE

    pygame.init()
    FPS_CLOCK = pygame.time.Clock()
    DISPLAY_SURFACE = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    MAIN_HINT = ' (press RETURN to re-set the start conditions or ESC to quit)'

    # set initial conditions for cells in grid
    cells = initialise_grid()

    gen_count = 0
    while True: # main game loop
        for event in pygame.event.get(): 
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()
                elif event.key == K_RETURN:
                    # re-set initial conditions for cells in grid
                    cells = initialise_grid()
                    gen_count = 0
                    
        # set title with hint
        pygame.display.set_caption(WINDOW_TITLE + MAIN_HINT + ' generation=' + str(gen_count))
        
        # apply game of life rules to the cells
        gen_count += 1
        cells = live_or_die(cells)

        DISPLAY_SURFACE.fill(BG_COLOUR)
        draw_grid_lines() # draw grid
        draw_cells(cells) # draw this generation of cells on the grid
        pygame.display.update()
        FPS_CLOCK.tick(FPS)


if __name__ == '__main__':
    main()
