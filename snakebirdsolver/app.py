#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

import sys
import numpy
import random
import colorama

# Check out THIS mess of inconsistently-named and weirdly-capitalized
# constants and lookup vars.  CLASSY.
#
# Apologies for this and all the other idiocy in this code; it's very
# much a Frankencreation which could use a full revamp.

DIR_U = 1
DIR_D = 2
DIR_L = 4
DIR_R = 8
DIRS = [DIR_U, DIR_D, DIR_L, DIR_R]
DIR_REV = {
    DIR_U: DIR_D,
    DIR_D: DIR_U,
    DIR_L: DIR_R,
    DIR_R: DIR_L,
}
DIR_T = {
    DIR_U: 'Up',
    DIR_D: 'Down',
    DIR_L: 'Left',
    DIR_R: 'Right',
}
DIR_CMD = {
    'w': DIR_U,
    's': DIR_D,
    'a': DIR_L,
    'd': DIR_R,
}
DIR_MODS = {
    DIR_U: (0, -1),
    DIR_D: (0, 1),
    DIR_L: (-1, 0),
    DIR_R: (1, 0),
}
DIR_MODS_REV = {}
for (k, v) in DIR_MODS.items():
    DIR_MODS_REV[v] = k

SNAKE_CHARS = {
    (DIR_U | DIR_D): '║',
    (DIR_U | DIR_L): '╝',
    (DIR_U | DIR_R): '╚',
    (DIR_L | DIR_R): '═',
    (DIR_D | DIR_L): '╗',
    (DIR_D | DIR_R): '╔',
}

(SNAKE_RED, SNAKE_BLUE, SNAKE_GREEN) = range(3)
SNAKE_T = {
    SNAKE_RED: 'Red',
    SNAKE_BLUE: 'Blue',
    SNAKE_GREEN: 'Green',
}
SNAKE_CHAR_MAP = {
    'R': SNAKE_RED,
    'G': SNAKE_GREEN,
    'B': SNAKE_BLUE,
}

# Cell types
(TYPE_EMPTY,
    TYPE_WALL,
    TYPE_SPIKE,
    TYPE_EXIT,
    TYPE_VOID,
    TYPE_TELEPORTER) = range(6)
TYPE_CHAR_MAP = {
    ' ': TYPE_EMPTY,
    'w': TYPE_WALL,
    '%': TYPE_SPIKE,
    'E': TYPE_EXIT,
    '~': TYPE_VOID,
    'T': TYPE_TELEPORTER,
}
TYPE_DISP_MAP = {
    TYPE_EMPTY: ' ',
    TYPE_WALL: '█',
    TYPE_SPIKE: '░',
    TYPE_EXIT: 'E',
    TYPE_VOID: '~',
    TYPE_TELEPORTER: 'T',
}

# Pushables
PUSH_CHARS = [ '▰', '▲', '▶', '▼', '◀', '◆', '◉', '◩', '◮', '◍' ]

# Pushable decoration char map
pushable_char_map = {
    '|': '│',
    '-': '─',
    '+': '┼',
    '>': '├',
    '<': '┤',
    '^': '┴',
    'V': '┬',
}

# Colors
color_wall = {
    TYPE_EMPTY: colorama.Style.RESET_ALL,
    TYPE_WALL: colorama.Fore.BLACK,
    TYPE_SPIKE: colorama.Fore.RED,
    TYPE_EXIT: colorama.Fore.MAGENTA,
    TYPE_VOID: colorama.Fore.RED,
    TYPE_TELEPORTER: colorama.Fore.BLUE,
}
color_fruit = colorama.Fore.CYAN
color_wall_exit_open = colorama.Fore.GREEN
color_wall_exit_closed = colorama.Fore.MAGENTA
color_snake = {
    SNAKE_RED: colorama.Fore.RED,
    SNAKE_BLUE: colorama.Fore.BLUE,
    SNAKE_GREEN: colorama.Fore.GREEN,
}
color_pushables = [
    colorama.Fore.WHITE+colorama.Back.YELLOW,
    colorama.Fore.WHITE+colorama.Back.MAGENTA,
    colorama.Fore.WHITE+colorama.Back.CYAN,
    colorama.Fore.WHITE+colorama.Back.RED,
    colorama.Fore.WHITE+colorama.Back.GREEN,
    colorama.Fore.WHITE+colorama.Back.BLUE,
    colorama.Fore.CYAN+colorama.Back.MAGENTA,
    colorama.Fore.CYAN+colorama.Back.BLUE,
    colorama.Fore.CYAN+colorama.Back.YELLOW,
    colorama.Fore.CYAN+colorama.Back.RED,
]
color_pushables_decoration = [
    colorama.Fore.YELLOW,
    colorama.Fore.MAGENTA,
    colorama.Fore.CYAN,
    colorama.Fore.RED,
    colorama.Fore.GREEN,
    colorama.Fore.BLUE,
    colorama.Fore.MAGENTA,
    colorama.Fore.BLUE,
    colorama.Fore.YELLOW,
    colorama.Fore.RED,
]

class PlayerLose(Exception):
    """
    Custom exception to handle player loss
    """

class Snakebird(object):
    """
    A Snakebird.  Internally this is mostly just a list which has (x,y)
    tuples in it.  Element zero is the head, element -1 is the tail.
    """

    supported_by_spikes = False

    def __init__(self, color, level):
        self.color = color
        self.level = level
        self.exited = False
        self.cells = []
        self.checksum_id = SNAKE_T[self.color][0]

    def __len__(self):
        return len(self.cells)

    def __str__(self):
        return SNAKE_T[self.color]

    def set_initial_cell(self, x, y):
        self.cells = [(x, y)]

    def finish(self, body_pointers):
        """
        Construct the rest of our body during level load
        """
        while self.cells[-1] in body_pointers:
            new_cell = body_pointers[self.cells[-1]]
            del body_pointers[self.cells[-1]]
            self.cells.append(new_cell)

    def compute_display_chars(self):
        """
        Loops through our body to determine what characters to print for
        each of our segments.  We're only doing this when explicitly
        displaying the level, since it's pointless computation if we're
        just running the solver.  This has the side-effect that our last
        segment isn't *technically* displayed properly, 'cause the display
        characters aren't keeping track of the previous state of the snake.
        So the snakebird's tail will end up straightening out where in
        the game it would've stayed bent, if that was the case.  Still,
        no actual gameplay impact there, so I don't care.
        """
        self.display_chars = [SNAKE_T[self.color][0]]
        for i in range(1,len(self)):
            dir_to_head = DIR_MODS_REV[tuple(numpy.subtract(self.cells[i-1], self.cells[i]))]
            if i+1 == len(self):
                dir_to_tail = DIR_REV[dir_to_head]
            else:
                dir_to_tail = DIR_MODS_REV[tuple(numpy.subtract(self.cells[i+1], self.cells[i]))]
            self.display_chars.append(SNAKE_CHARS[dir_to_head | dir_to_tail])

    def get_print_char(self, idx):
        """
        Given the passed-in index, return the printing char
        we should use if we're printing out to a console.
        """
        return '{}{}'.format(color_snake[self.color], self.display_chars[idx])

    def get_possible_moves(self):
        """
        Returns a list of possible moves for us
        """
        ret_dirs = []
        if self.exited:
            return ret_dirs
        for direction in DIRS:
            (coords, cell_type) = self.level.get_cell_dir(self.cells[0], direction)
            if coords in self.level.snake_coords:
                if self.level.snake_coords[coords] != self:
                    other_sb = self.level.snake_coords[coords]
                    (ss, supported, danger_spikes, danger_void) = other_sb.get_adjacents(direction, self)
                    if not supported and not danger_spikes and not danger_void and self not in ss:
                        ret_dirs.append(direction)
            else:
                if cell_type != TYPE_WALL and cell_type != TYPE_SPIKE:
                    ret_dirs.append(direction)
        return ret_dirs

    def push(self, direction, other_snakes):
        """
        We were pushed in the specified direction.  We're going to assume
        that the push was valid so we're not doubling up on processing.
        Pass in `other_snakes` to prevent a double-push from happening
        """
        #self.cells = [tuple(numpy.add(c, DIR_MODS[direction])) for c in self.cells]
        teleport_idx = None
        for (idx, c) in enumerate(self.cells.copy()):
            self.cells[idx] = tuple(numpy.add(c, DIR_MODS[direction]))
            if self.cells[idx] in self.level.teleporter:
                teleport_idx = idx

        # TODO: Potential race condition with teleports here - what happens if more than
        # one snake gets pushed into a teleport on the same turn?  Well, actually I suppose
        # I know the answer, sort of - neither should teleport because it'd be blocked.
        # We should maybe make sure that's the case, though.  Will look into it if I find
        # a level where it could happen.

        # Check to see if we're pushed another snake
        other_snakes.add(self)
        for cell in self.cells:
            if (cell in self.level.snake_coords and
                    self.level.snake_coords[cell] != self and
                    self.level.snake_coords[cell] not in other_snakes):
                sb = self.level.snake_coords[cell]
                other_snakes.add(sb)
                sb.push(direction, other_snakes)

        # TODO: I wonder what would happen first - exit or teleport?

        # Check to see if we were pushed into an exit.  We couldn't win
        # in this circumstance because the other snake that just pushed us
        # couldn't reach the exit yet.
        if self.level.cells[self.cells[0][1]][self.cells[0][0]] == TYPE_EXIT and len(self.level.fruits) == 0:
            self.exited = True
            self.cells = []

        # Finally, if we were pushed into a teleporter, take care of that.
        if teleport_idx is not None:
            self.process_teleport(teleport_idx)

    def process_teleport(self, index):
        """
        Processes a teleport of ourselves, with the teleporter at the given index
        """

        # Grab our current teleporter and find out if it's active.  Return right
        # away if not.
        cur_pivot = self.cells[index]
        if self.level.teleporter_occupied[cur_pivot] == self:
            return

        # Grab the new teleporter and find out if it's available.  Return right
        # away if not.
        new_pivot = self.level.teleporter[cur_pivot]
        if new_pivot in self.level.snake_coords:
            self.level.teleporter_occupied[cur_pivot] = self
            return

        # Now find out if we "fit" in the new location or not
        new_cells = []
        for cell in self.cells:
            new_cell = (
                cell[0]-self.cells[index][0]+new_pivot[0],
                cell[1]-self.cells[index][1]+new_pivot[1]
                )
            cell_type = self.level.cells[new_cell[1]][new_cell[0]]
            if (new_cell in self.level.snake_coords or new_cell in self.level.fruits or
                    (cell_type != TYPE_EMPTY and cell_type != TYPE_EXIT and
                        cell_type != TYPE_TELEPORTER)):
                # We'd be blocked, so don't teleport!
                self.level.teleporter_occupied[cur_pivot] = self
                return False
            new_cells.append(new_cell)

        # If we got here, we're good to teleport
        self.cells = new_cells
        self.level.teleporter_occupied[cur_pivot] = None
        self.level.teleporter_occupied[new_pivot] = self
        return True

    def move(self, direction):
        """
        Attempts to move us in the specified direction
        """
        (coords, cell_type) = self.level.get_cell_dir(self.cells[0], direction)
        if coords in self.level.snake_coords:
            if self.level.snake_coords[coords] != self:
                # NOTE!  To avoid extra processing, we are blindly assuming
                # that this is a valid, unblocked push that we're doing.
                # Theoretically all our code previously (get_possible_moves, etc)
                # has already verified all that, so we're going to blindly
                # trust it.
                self.level.snake_coords[coords].push(direction, set([self]))

                # After pushing the snake, process as usual.  There could have
                # been an exit hiding behind the snake.  (The check for fruit
                # is meaningless as we couldn't have been hiding that, but whatever.)

        if coords in self.level.fruits:
            self.level.consume_fruit(coords)
            self.cells.insert(0, coords)
            self.level.populate_snake_coords()
            return self.level.check_fall()
        elif cell_type == TYPE_EMPTY or cell_type == TYPE_EXIT or cell_type == TYPE_TELEPORTER:
            self.cells.pop()
            self.cells.insert(0, coords)
            if cell_type == TYPE_EXIT and len(self.level.fruits) == 0:
                self.exited = True
                self.cells = []
                if self.level.check_win():
                    return True
                else:
                    self.level.populate_snake_coords()
                    return self.level.check_fall()
            else:
                if cell_type == TYPE_TELEPORTER:
                    self.process_teleport(0)
                self.level.populate_snake_coords()
                return self.level.check_fall()
        else:
            self.level.populate_snake_coords()

    def get_adjacents(self, direction, falling=False, calling_snake=None, recurse=True):
        """
        Get a set of items that we're adjacent to (which could
        theoretically be blocking us if we're falling, or prevent
        us from being pushed, etc).  `falling` is a boolean
        specifying whether we're falling (or pushing, alternatively).
        This matters for interactions between snakebirds.

        Returns a tuple of the following:

        (snakesupports, supported, spikes, void)

        The first element, `snakesupports`, is a list of all
        snakebirds that are possibly "supporting" ourself.  `supported`
        is a boolean indicating whether we've got something solid
        (wall, fruit).  `spikes` is a boolean indicating spikes,
        `void` is a boolean indicating void..

        For snakes being pushed, you'd be blocked by supported OR
        spikes/void.  For snakes falling, spikes/void would mean death unless
        you're also supported.
        """
        # Fruit is always a "platform" even if you're pushing
        # another snake into it; I think the first place you can see
        # that easily is level 26

        # TODO:
        # Our "snakesupports" stuff fails when more complex pushable objects
        # are in play.  For instance, this situation in level 25:
		#    
		#    ~        ▰     ~ 
		#    ~      ███     ~ 
		#    ~      ▰B══▰   ~ 
		#    ~       ╔G     ~ 
		#    ~      ═╝▰     ~ 
        #    ~     █   █    ~ 
        #
        # Blue can't push left because the object sees that blue is to the
        # left of the object's rightmost cell, even though it's allowed in-game.
        #
        # Eh, I'm thinking a proper solution to this may be difficult.  If
        # blue was one more segment long and had a tail pointing down, the
        # game would NOT allow the move, meaning that this is an entirely
        # different case than we've looked at thus far.

        # TODO:
        # Another case where pushable objects seem different than dealing with
        # other snakes, unless I've just gotten this wrong the whole time
        # somehow.  Level 39:
        #
        #    ~           ████     ~ 
        #    ~     ╔═    █████    ~ 
        #    ~     ║▰▰    ████    ~ 
        #    ~     ╚G▲▲  █████    ~ 
        #    ~    ████  ██████    ~ 
        #
        # In our solver, Green can only go right, but in Snakebird itself,
        # green can go up and it works like you'd hope.  This turns out to not
        # actually affect the puzzle solution, but it's something that should
        # probably be taken care of.

        # TODO:
        # This is all quite inefficient

        snakesupports = set()
        supported = False
        spikes = False
        void = False
        for coords in self.cells:
            (other_coords, other_type) = self.level.get_cell_dir(coords, direction)
            if other_coords in self.level.snake_coords:
                if self.level.snake_coords[other_coords] != self:
                    snakesupports.add(self.level.snake_coords[other_coords])
                    # If we're being pushed and a cell of our pushing snake is in
                    # the way, consider ourself blocked
                    if not falling and self.level.snake_coords[other_coords] == calling_snake:
                        supported = True
            elif other_coords in self.level.fruits:
                supported = True
            elif other_type == TYPE_WALL:
                supported = True
            elif other_type == TYPE_SPIKE:
                spikes = True
                if self.supported_by_spikes:
                    supported = True
            elif other_type == TYPE_VOID:
                void = True

        # Conditions on which we'll return right away:
        #  1) If we've been called from another snake and aren't recursing
        #  2) If we have no snake supports
        #  3) We have a direct support
        #  4) We're not falling and have a 'danger'
        if ((calling_snake and not recurse) or
                len(snakesupports) == 0 or
                supported or
                (not falling and (spikes or void))):
            return (snakesupports, supported, spikes, void)

        # If we got here, we need to get more info from our snake supports
        seen_snakes = set()
        seen_snakes.add(self)
        continue_looping = True
        new_ss = snakesupports.copy()
        while continue_looping:
            continue_looping = False
            if not supported:
                for sb in new_ss.copy():
                    new_ss = set()
                    if sb not in seen_snakes:
                        seen_snakes.add(sb)
                        snakesupports.add(sb)
                        (other_ss, other_supported, other_spikes, other_void) = sb.get_adjacents(
                            direction, falling=falling, calling_snake=self, recurse=False)
                        if other_supported:
                            supported = True
                            break
                        if not spikes and other_spikes:
                            spikes = True
                        if not void and other_void:
                            void = True
                        for ss in other_ss:
                            if ss not in seen_snakes:
                                new_ss.add(ss)
                                continue_looping = True

        # Return...
        return (snakesupports, supported, spikes, void)

    def fall(self):
        """
        Fall!  Could potentially be a no-op, of course.  Make sure to keep this
        function in-line with Pushable.fall()
        """

        if self.exited:
            return

        supported = False
        supported_by_spikes = False
        supported_by_void = False

        # Find out what's beneath us
        (snakesupports,
            supported,
            supported_by_spikes,
            supported_by_void) = self.get_adjacents(DIR_D, falling=True)

        # Check to see if we fall, or are dead, or whatever
        if supported:
            return False
        elif supported_by_spikes or supported_by_void:
            raise PlayerLose('Fell to your death!')
        else:
            for sb in [self] + list(snakesupports):
                #sb.cells = [tuple(numpy.add(c, DIR_MODS[DIR_D])) for c in sb.cells]
                teleport_idx = None
                for (idx, c) in enumerate(sb.cells.copy()):
                    sb.cells[idx] = tuple(numpy.add(c, DIR_MODS[DIR_D]))
                    if sb.cells[idx] in self.level.teleporter:
                        teleport_idx = idx

                # TODO: I wonder what would happen first - exit or teleport?

                # Check to see if we exited - this can happen in the middle
                # of a fall (I think level 4 is the first where we can
                # conclusively say this)
                if self.level.cells[sb.cells[0][1]][sb.cells[0][0]] == TYPE_EXIT and len(self.level.fruits) == 0:
                    sb.exited = True
                    sb.cells = []

                # If we were pushed into a teleporter, take care of that.
                if teleport_idx is not None:
                    sb.process_teleport(teleport_idx)

            # We fell, so return true
            return True

    def clone(self):
        newobj = Snakebird(self.color, self.level)
        newobj.cells = list(self.cells)
        newobj.exited = self.exited
        return newobj

    def apply_clone(self, newobj):
        self.cells = []
        self.cells = list(newobj.cells)
        self.exited = newobj.exited

    def checksum(self):
        return ','.join([str(c) for c in self.cells])

class Pushable(Snakebird):
    """
    A pushable object.  We're subclassing Snakebird because there's
    enough in common (specifically get_adjancents() and push()) which
    we'd otherwise have to just copy+paste into here.
    """

    supported_by_spikes = True

    def __init__(self, desc, level):
        self.desc = desc
        self.level = level
        self.cells = []
        self.cells_decoration = []
        self.checksum_id = desc

    def __str__(self):
        return 'Pushable {}'.format(self.desc)

    def add_cell(self, x, y):
        """
        Adds the given coordinate as a cell.
        """
        self.cells.append((x,y))

    def add_cell_decoration(self, rel_x, rel_y, char):
        """
        Adds a 'relative' decoration cell, coords based on the first
        real cell.  Will be translated into actual cells during level
        display.
        """
        if char not in pushable_char_map:
            raise Exception('Pushable decoration char not known: {}'.format(char))
        self.cells_decoration.append(((rel_x, rel_y), pushable_char_map[char]))

    def get_decoration_chars(self):
        """
        Returns a dict with keys being coordinates and values being the character
        to print at the coord.  Will use self.cells_decoration as offsets based on
        the first cell in self.cells.  We're setting some display colors here
        as well, which is a bit improper, but this is only used in display anyway,
        so whatever.
        """
        ret_dict = {}
        if len(self.cells) > 0:
            for ((rel_x, rel_y), disp_char) in self.cells_decoration:
                ret_dict[(self.cells[0][0]+rel_x, self.cells[0][1]+rel_y)] = '{}{}{}'.format(
                    color_pushables_decoration[self.desc],
                    disp_char,
                    colorama.Style.RESET_ALL,
                )
        return ret_dict

    def fall(self):
        """
        Fall!  Could potentially be a no-op, of course.  Returns `True` if we fell,
        `False` otherwise.  (Note that we return `False` if we were destroyed by
        a void tile, as well).  Make sure to keep this function in-line with
        Snakebird.fall().
        """

        if len(self.cells) == 0:
            return

        supported = False
        supported_by_spikes = False
        supported_by_void = False

        # Find out what's beneath us
        (snakesupports,
            supported,
            supported_by_spikes,
            supported_by_void) = self.get_adjacents(DIR_D, falling=True)

        # Check to see if we fall, or disappear, or whatever
        if supported or supported_by_spikes:
            return False
        elif supported_by_void:
            self.cells = []
            if self.level.die_on_pushable_loss:
                raise PlayerLose('Lost a pushable object!')
            return False
        else:

            for sb in [self] + list(snakesupports):
                #sb.cells = [tuple(numpy.add(c, DIR_MODS[DIR_D])) for c in sb.cells]
                teleport_idx = None
                for (idx, c) in enumerate(sb.cells.copy()):
                    sb.cells[idx] = tuple(numpy.add(c, DIR_MODS[DIR_D]))
                    if sb.cells[idx] in self.level.teleporter:
                        teleport_idx = idx
                if teleport_idx is not None:
                    sb.process_teleport(teleport_idx)

            # We fell, so return true
            return True

    def clone(self):
        newobj = Pushable(self.desc, self.level)
        newobj.cells = list(self.cells)
        newobj.cells_decoration = list(self.cells_decoration)
        return newobj

    def apply_clone(self, newobj):
        self.cells = []
        self.cells = list(newobj.cells)
        self.cells_decoration = list(newobj.cells_decoration)

    def checksum(self):
        if len(self.cells) == 0:
            return '-'
        else:
            return str(self.cells[0])

class Level(object):

    def __init__(self, filename):

        self.cells = []
        # TODO: I'm not sure it actually makes sense to have a
        # snakebirds dict.  I think we don't ever *actually* use
        # it.
        self.snakebirds = {}
        self.snakebirds_l = []
        # TODO: self.fruits should probably be a set()
        self.fruits = {}
        self.pushables = {}
        self.interactives = []
        body_pointers = {}
        self.won = False
        self.max_defined_steps = 100
        self.return_first_solution = False
        self.preferred_algorithm = 'BFS'
        self.die_on_pushable_loss = True
        self.teleporter = {}
        self.teleporter_occupied = {}

        # We give ourselves room around the outside of the map
        # in case solutions involve going outside the level
        # boundaries.
        self.padding_x = 5
        self.padding_y = 2
        self.max_seen_x = 0
        self.max_seen_y = 0

        # Read in the whole file
        have_exit = False
        with open(filename, 'r') as df:

            key = ''
            while key != 'level':

                # Grab the next line
                line = df.readline().strip()
                if ': ' in line:
                    (key, value) = line.split(': ', 1)
                else:
                    key = line
                    value = None
                key = key.lower()

                # Figure out what sort of data it is
                if key == 'alg':
                    if value.upper() not in ['DFS', 'BFS']:
                        raise Exception('Unknown preferred algorithm: {}'.format(value))
                    self.preferred_algorithm = value.upper()

                elif key == 'exitonfirst':
                    self.return_first_solution = True

                elif key == 'allowpushableloss':
                    self.die_on_pushable_loss = False

                elif key == 'max':
                    self.max_defined_steps = int(value)

                elif key == 'level':
                    self.desc = 'Level {}'.format(value)

                elif key[:11] == 'decoration ':
                    num = int(key[11:])
                    if num > 9:
                        raise Exception('Pushable numbers cannot exceed 9, currently')
                    if num in self.pushables:
                        obj = self.pushables[num]
                    else:
                        obj = Pushable(num, self)
                        self.pushables[num] = obj
                        self.interactives.append(obj)
                    first_cell = None
                    rows = int(value)
                    for y in range(rows):
                        for (x, char) in enumerate(df.readline().rstrip()):
                            if char == 'O':
                                if first_cell is None:
                                    first_cell = (x, y)
                            elif char == ' ':
                                pass
                            elif first_cell is None:
                                raise Exception('Pushable decoration chars can only appear after a "real" cell is found')
                            else:
                                obj.add_cell_decoration(x-first_cell[0], y-first_cell[1], char)
                else:
                    raise Exception('Unknown tag in map data: {}'.format(key))

            # If we're here, we got the 'Level' tag, so we should start reading
            # level data.
            teleporter_1 = None
            teleporter_2 = None
            for (y, line) in enumerate(df.readlines()):
                y += self.padding_y
                line = line.rstrip()
                for (x, char) in enumerate(line):
                    x += self.padding_x
                    if char in TYPE_CHAR_MAP.keys():
                        self.set_map_char(x, y, char)
                        if char == 'E':
                            if have_exit:
                                raise Exception('More than one exit found!')
                            else:
                                have_exit = True
                        elif char == 'T':
                            if teleporter_1 is None:
                                teleporter_1 = (x,y)
                            elif teleporter_2 is None:
                                teleporter_2 = (x,y)
                                self.teleporter[teleporter_1] = teleporter_2
                                self.teleporter[teleporter_2] = teleporter_1
                                self.teleporter_occupied[teleporter_1] = None
                                self.teleporter_occupied[teleporter_2] = None
                            else:
                                raise Exception('More than two teleporters found!')
                    elif char == 'F':
                        self.fruits[(x,y)] = True
                    elif char in SNAKE_CHAR_MAP.keys():
                        color = SNAKE_CHAR_MAP[char]
                        sb = Snakebird(color, self)
                        sb.set_initial_cell(x,y)
                        self.snakebirds[color] = sb
                        self.snakebirds_l.append(sb)
                        self.interactives.append(sb)
                    elif char == 'V':
                        body_pointers[(x,y+1)] = (x,y)
                    elif char == '>':
                        body_pointers[(x+1,y)] = (x,y)
                    elif char == '<':
                        body_pointers[(x-1,y)] = (x,y)
                    elif char == '^':
                        body_pointers[(x,y-1)] = (x,y)
                    else:
                        try:
                            char_int = int(char)
                            if char_int not in self.pushables.keys():
                                new_obj = Pushable(char_int, self)
                                self.pushables[char_int] = new_obj
                                self.interactives.append(new_obj)
                            self.pushables[char_int].add_cell(x, y)
                        except ValueError as e:
                            raise Exception('Unknown char at {},{}: {}'.format(
                                x-self.padding_x, y-self.padding_y, char
                            ))

            # Add padding at the bottom
            self.set_map_char(self.max_seen_x + self.padding_x,
                self.max_seen_y + self.padding_y, ' ')

            # And finally, put a "void" border around the whole map.  We only really
            # need one on the bottom, but this will prevent us from having to check
            # bounds while pushing snakebirds on the edges of the map, etc.
            for x in range(self.max_seen_x-1):
                self.set_map_char(x, self.max_seen_y-2, '~')
                self.set_map_char(x, 0, '~')
            for y in range(self.max_seen_y-1):
                self.set_map_char(0, y, '~')
                self.set_map_char(self.max_seen_x-2, y, '~')

        # Construct our Snakebirds
        for sb in self.snakebirds.values():
            sb.finish(body_pointers)

        # Make sure we've used up all our body pointers
        if len(body_pointers) > 0:
            raise Exception('Not all body pointers were used up!')

        # Make sure we have at least one snakebird
        if len(self.snakebirds) == 0:
            raise Exception('No snakebirds found in level!')

        # Make sure that all our pushables have at least one cell
        for obj in self.pushables.values():
            if len(obj.cells) == 0:
                raise Exception('Pushable Object {} has no cells defined (probably decoration/pushable ID mismatch)'.format(obj.desc))

        # Make sure that if we have one teleporter cell, we have two
        if teleporter_1 is not None and teleporter_2 is None:
            raise Exception('Only one teleporter found in level!')

        # Aaand populate our snake_coords dict
        self.populate_snake_coords()

    def set_map_char(self, x, y, char):
        """
        Sets the given map coordinate to the given char, expanding the map geometry
        as we go.  Only used during map creation.  Possibly a bit silly to have it
        as a function instead of inline.
        """

        # Create new rows we haven't seen yet
        added_rows = False
        for idx in range(y-self.max_seen_y+1):
            self.cells.append([TYPE_EMPTY]*self.max_seen_x)
            added_rows = True
        if added_rows:
            self.max_seen_y = y + 1
        
        # Create new columns we haven't seen yet
        added_cols = False
        for row in self.cells:
            for idx in range(x-self.max_seen_x+1):
                row.append(TYPE_EMPTY)
                added_cols = True
        if added_cols:
            self.max_seen_x = x + 1
        
        # Now set our type
        self.cells[y][x] = TYPE_CHAR_MAP[char]

    def check_win(self):
        """
        Check to see if we've won
        """
        for sb in self.snakebirds_l:
            if not sb.exited:
                return False
        self.won = True
        return True

    def populate_snake_coords(self):
        """
        Populates our var which keeps track of which coordinates snakes
        are occupying.  Also keeps track of our teleporter, if we have
        one.
        """

        # Update snake coords
        self.snake_coords = {}
        for sb in self.interactives:
            for coords in sb.cells:
                self.snake_coords[coords] = sb

        # Also mark our teleporter as available if nothing's touching
        # it.
        for tp_coord in self.teleporter.keys():
            if tp_coord in self.snake_coords:
                self.teleporter_occupied[tp_coord] = self.snake_coords[tp_coord]
            else:
                self.teleporter_occupied[tp_coord] = None

    def get_cell_dir(self, coords, direction):
        """
        Returns the a tuple of ((x, y), type) of the cell in the given direction
        from the passed-in starting point
        """
        (new_x, new_y) = tuple(numpy.add(coords, DIR_MODS[direction]))
        return((new_x, new_y), self.cells[new_y][new_x])

    def consume_fruit(self, coords):
        """
        A snake ate one of our fruits
        """
        del self.fruits[coords]

    def check_fall(self):
        """
        Loops through our interactives and tell them to fall.  Will
        continue doing this while objects fall.  Also will check for
        a win condition after each round of falling, in case we win
        mid-fall, and will return `True` if we won.  (`False` otherwise)
        """
        # TODO: this is pretty inefficient - the individual calls to fall()
        # can cause more than one object to fall, but this loop doesn't really
        # know about that, so we can end up checking multiple times.  Of course,
        # that might be necessary anyway, but still.
        falling = set(self.interactives)
        while len(falling) > 0:
            for sb in falling.copy():
                if sb.fall():
                    self.populate_snake_coords()
                else:
                    falling.remove(sb)
            if self.check_win():
                return True
        return False

    def get_possible_moves(self):
        """
        Returns a list of all possible moves on the board, for all
        snakebirds.  Moves are a tuple of (sb, dir)
        """
        ret_list = []
        for sb in self.snakebirds.values():
            for direction in sb.get_possible_moves():
                ret_list.append((sb, direction))
        return ret_list

    def print_level(self):
        """
        Prints out our level
        """

        # First grab information about our snakes
        disp_snake_coords = {}
        for sb in self.snakebirds.values():
            sb.compute_display_chars()
            for (idx, coords) in enumerate(sb.cells):
                disp_snake_coords[coords] = (sb, idx)

        # Grab information about pushables and pushable decorations
        disp_pushable_coords = {}
        disp_pushable_decorations = {}
        for (push_num, pushable) in self.pushables.items():
            for coords in pushable.cells:
                disp_pushable_coords[coords] = '{}{}{}'.format(
                        color_pushables[push_num],
                        PUSH_CHARS[push_num],
                        colorama.Style.RESET_ALL,
                    )
            disp_pushable_decorations.update(pushable.get_decoration_chars())

        # Find out what color our exit should be
        if len(self.fruits) == 0:
            color_wall[TYPE_EXIT] = color_wall_exit_open
        else:
            color_wall[TYPE_EXIT] = color_wall_exit_closed

        # Now loop through and print the level
        print(self.desc)
        for (y, row) in enumerate(self.cells):
            for (x, col) in enumerate(row):
                if (x,y) in disp_snake_coords:
                    (sb, idx) = disp_snake_coords[(x,y)]
                    sys.stdout.write(sb.get_print_char(idx))
                elif (x,y) in disp_pushable_coords:
                    sys.stdout.write(disp_pushable_coords[(x,y)])
                elif (x,y) in self.fruits:
                    sys.stdout.write('{}{}'.format(color_fruit, 'F'))
                elif col == TYPE_EMPTY and (x, y) in disp_pushable_decorations:
                    sys.stdout.write(disp_pushable_decorations[(x,y)])
                else:
                    sys.stdout.write('{}{}'.format(color_wall[col], TYPE_DISP_MAP[col]))
            sys.stdout.write("{}\n".format(colorama.Style.RESET_ALL));

    def print_debug_info(self):
        """
        Print all information about ourselves - used if we catch an exception somewhere.
        """
        self.print_level()
        for sb in self.snakebirds_l:
            print('Snakebird {}: {}'.format(str(sb), sb.cells))
        for fruit in self.fruits.keys():
            print('Fruit: {}'.format(fruit))
        print('Level SB coords:')
        for (coord, sb) in self.snake_coords.items():
            print('  {}: {}'.format(str(sb), coord))
        for obj in self.pushables.values():
            print('{}: {}'.format(str(obj), obj.cells))
        if (len(self.teleporter) > 0):
            print('Teleporter coords: {}'.format(self.teleporter))
            for (coord, occupier) in self.teleporter_occupied.items():
                print('   {}: {}'.format(coord, str(occupier)))

class State(object):

    def __init__(self, level, moves=None):

        self.level = level
        self.fruits = {}
        self.snakebirds = {}
        self.pushables = {}
        self.moves = moves
        self.teleporter_occupied = level.teleporter_occupied.copy()

        for coord in level.fruits.keys():
            self.fruits[coord] = True
        # TODO: I feel these could be combined...
        for (color, sb) in level.snakebirds.items():
            self.snakebirds[color] = sb.clone()
        for (num, obj) in level.pushables.items():
            self.pushables[num] = obj.clone()

    def apply(self):

        self.level.fruits = {}
        for coords in self.fruits.keys():
            self.level.fruits[coords] = True

        for color in self.snakebirds.keys():
            self.level.snakebirds[color].apply_clone(self.snakebirds[color])

        for num in self.pushables.keys():
            self.level.pushables[num].apply_clone(self.pushables[num])

        self.level.populate_snake_coords()

        self.level.teleporter_occupied = self.teleporter_occupied.copy()

        if self.moves is not None:
            return list(self.moves)

    def checksum(self):

        sumlist = []
        if len(self.level.teleporter) > 0:
            for (idx, (coord, occupier)) in enumerate(self.level.teleporter_occupied.items()):
                if occupier is None:
                    sumlist.append('t{}=-'.format(idx))
                else:
                    sumlist.append('t{}={}'.format(idx, occupier.checksum_id))
        for fruit in self.fruits.keys():
            sumlist.append('f={}'.format(fruit))
        # TODO: Ditto re: combination
        for sb in self.snakebirds.values():
            sumlist.append('s-{}={}'.format(sb.color, sb.checksum()))
        for obj in self.pushables.values():
            sumlist.append('p-{}={}'.format(obj.desc, obj.checksum()))
        return '|'.join(sumlist)

class Game(object):
    
    def __init__(self, filename):

        # Save the level
        self.level = Level(filename)

        # Current snakebird
        self.cur_snakebird_idx = 0
        self.cur_snakebird = self.level.snakebirds_l[0]

        # Max steps
        self.max_steps = self.level.max_defined_steps
        self.cur_steps = 0

        # And a list for states
        self.states = []

        # List of moves
        self.moves = []

        # Best solution found
        self.solution = None
        
        # Death state
        self.alive = True

        # Seen checksums
        self.checksums = {}

    def push_state(self, state=None):
        if state is None:
            state = State(self.level)
        self.states.append(state)

    def get_state(self, moves=None):
        """
        Get our state.  Optionally pass in `moves` if you're using
        a BFS solver and need to hold on to moves
        """
        state = State(self.level, moves)
        checksum = state.checksum()
        if checksum in self.checksums:
            if self.cur_steps >= self.checksums[checksum]:
                return (state, False)
        self.checksums[checksum] = self.cur_steps
        return (state, True)

    def pop_state(self):
        state = self.states.pop()
        state.apply()

    def move(self, sb, direction, state=None):
        self.moves.append((sb, direction))
        self.push_state(state)
        self.cur_steps += 1
        return sb.move(direction)

    def undo(self):
        if len(self.states) > 0:
            self.moves.pop()
            self.pop_state()
            self.cur_steps -= 1
            self.level.won = False
            self.alive = True
        else:
            print('No undo states!')

    def step_limit(self):
        if self.max_steps is None:
            return False
        else:
            if self.cur_steps >= self.max_steps:
                return True
            else:
                return False

    def print_winning_move_set(self, move_set):
        print('Winning moves ({}) for {}:'.format(len(move_set), self.level.desc))
        for (n, (sb, move)) in enumerate(move_set):
            print("\t{}. {}: {}".format(n+1, SNAKE_T[sb.color], DIR_T[move]))

    def store_winning_moves(self, quiet=False, display_moves=True):
        if not quiet:
            print('Found winning solution with {} moves'.format(len(self.moves)))
        self.max_steps = len(self.moves)-1
        if self.solution is None or len(self.moves) < len(self.solution):
            self.solution = []
            for direction in self.moves:
                self.solution.append(direction)
        if not quiet and display_moves:
            self.print_winning_move_set(self.moves)

    def print_status(self):
        self.level.print_level()
        snakebirds_active = 0
        for sb in self.level.snakebirds_l:
            if not sb.exited:
                snakebirds_active += 1
        print('Fruit left: {} | Snakebirds active: {} | Moves: {}'.format(
            len(self.level.fruits),
            snakebirds_active,
            self.cur_steps,
            ))
        if self.level.won:
            print('You win!')
            print('')
            self.store_winning_moves(display_moves=True)
        elif self.alive == False:
            print('You have lost.')
        else:
            print('Controlling {}{} Snakebird{}'.format(
                color_snake[self.cur_snakebird.color],
                SNAKE_T[self.cur_snakebird.color],
                colorama.Style.RESET_ALL
            ))
            if (len(self.level.get_possible_moves()) == 0):
                print('{}No moves available!{}'.format(colorama.Fore.RED, colorama.Style.RESET_ALL))
            else:
                print('Possible moves:')
                moves = self.cur_snakebird.get_possible_moves()
                if len(moves) == 0:
                    print("\t{}None!{}".format(colorama.Fore.RED, colorama.Style.RESET_ALL))
                else:
                    for direction in self.cur_snakebird.get_possible_moves():
                        print("\t{}".format(DIR_T[direction]))

    def interactive(self):
        colorama.init(autoreset=True)
        while True:
            self.cur_snakebird = self.level.snakebirds_l[self.cur_snakebird_idx]
            if not self.level.won and self.alive and len(self.level.get_possible_moves()) > 0:
                while self.cur_snakebird.exited == True:
                    self.cur_snakebird_idx = ((self.cur_snakebird_idx + 1) % len(self.level.snakebirds))
                    self.cur_snakebird = self.level.snakebirds_l[self.cur_snakebird_idx]
            self.print_status()
            full_control = True
            if self.level.won:
                return True
            elif self.alive == False or len(self.level.get_possible_moves()) == 0:
                full_control = False

            if full_control:
                print('[wasd] - movement, [c]hange snakebirds, [u]ndo, [r]eset, [q]uit, [i]nfo')
            else:
                print('[u]ndo, [r]eset, [q]uit, [i]nfo')
            sys.stdout.write('[{}] > '.format(self.cur_steps + 1))
            sys.stdout.flush()
            cmd = sys.stdin.readline()
            cmd = cmd.strip()
            if cmd == '':
                continue
            cmd = cmd[0].lower()

            direction = None
            if cmd == 'q':
                return False
            elif cmd == 'u':
                self.undo()
            elif cmd == 'r':
                while len(self.states) > 0:
                    self.undo()
            elif cmd == 'i':
                self.print_debug_info()
            elif full_control and cmd == 'c':
                self.cur_snakebird_idx = ((self.cur_snakebird_idx + 1) % len(self.level.snakebirds))
                while self.level.snakebirds_l[self.cur_snakebird_idx].exited == True:
                    self.cur_snakebird_idx = ((self.cur_snakebird_idx + 1) % len(self.level.snakebirds))
            elif full_control and cmd in DIR_CMD:
                direction = DIR_CMD[cmd]
                if direction in self.cur_snakebird.get_possible_moves():
                    try:
                        self.move(self.cur_snakebird, DIR_CMD[cmd])
                    except PlayerLose as e:
                        self.alive = False
                        report_str = 'Player Death: {}'.format(e)
                        print('-'*len(report_str))
                        print(report_str)
                        print('-'*len(report_str))

    def solve_recurs(self):
        """
        Recursive depth-first solver algorithm.  In most cases, especially
        levels with a single snakebird, the breadth-first search (below)
        is faster, though sometimes this one happens to win out, probably
        just due to luck.

        For multi-snakebird solutions, we randomize our move choice before
        looping through, to try and encourage snakebirds to move in tandem.
        Otherwise we're likely to exhaust our max_steps moving a single
        snakebird around before we even move the other.  This, of course,
        adds some CPU processing time to each iteration since we're calling
        a PRNG, but after very limited testing it seems to be worth it.

        Unless a level has `return_first_solution` defined, we'll continue
        to refine solutions until we've found the shortest one.  (Though
        of course a level may have more than one solution with the same
        number of moves.  For single snakebird levels, we'll always return
        the same one here, but it may be different in multi-snakebird levels,
        thanks to the randomization mentioned above.)
        """

        if len(self.level.snakebirds) > 1:
            do_shuffle = True
        else:
            do_shuffle = False

        if self.level.return_first_solution and self.solution is not None:
            return
        (state, new_checksum) = self.get_state()
        if not new_checksum:
            return
        moves = self.level.get_possible_moves()
        if do_shuffle:
            random.shuffle(moves)
        for (sb, direction) in moves:
            try:
                if (self.move(sb, direction, state)):
                    self.store_winning_moves(quiet=False, display_moves=False)
                    if self.level.return_first_solution:
                        return
                    self.undo()
                else:
                    if self.step_limit():
                        self.undo()
                    else:
                        self.solve_recurs()
                        self.undo()
            except PlayerLose:
                self.undo()

    def solve_bfs(self):
        """
        Our attempt at a breadth-first solver, inspired on
        https://github.com/david-westreicher/snakebird

        Note that that solver is probably faster than ours
        in general 'cause it's not so bogged down by spurious
        classes, etc.  I suspect its overall implementation
        is more efficient in all sorts of ways.  Ah well!

        In most cases, this is going to be faster than our
        original recursive (DFS) implementation.  It still runs
        into problems with multi-snake puzzles (as does David
        Westreicher's version) when the step count is high
        and there's not enough death situations to trim the
        tree down.

        Occasionally our original method is quicker, though.

        By definition, a solution found here will be the shortest
        one available, though a level could have multiple solutions
        with the same length.  This method should always return
        the same one, though, even for multi-snakebird levels (unlike
        our DFS solver).
        """
        queue = [self.get_state(self.moves)[0]]
        for i in range(self.max_steps):
            next_queue = []
            sys.stdout.write("\rAt depth: {}...".format(i))
            sys.stdout.flush()
            for state in queue:
                self.moves = state.apply()
                moves = self.level.get_possible_moves()
                for (sb, direction) in moves:
                    self.moves = state.apply()
                    try:
                        if (self.move(sb, direction, state)):
                            print('')
                            self.store_winning_moves(quiet=False, display_moves=False)
                            return
                        (new_state, is_new_state) = self.get_state(self.moves)
                        if is_new_state:
                            next_queue.append(new_state)
                    except PlayerLose:
                        pass
            queue = next_queue
            if len(next_queue) == 0:
                break
        print('')

    def print_debug_info(self, e=None):
        """
        Prints debugging info about ourselves, useful when handling
        exceptions.
        """
        if e is not None:
            print('Captured an Exception: {}'.format(str(e)))
        self.level.print_debug_info()
        print('Current list of moves:')
        for (n, (sb, move)) in enumerate(self.moves):
            print("\t{}. {}: {}".format(n+1, SNAKE_T[sb.color], DIR_T[move]))
        print('(end)')
        print('')
