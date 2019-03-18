#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4 fileencoding=utf-8:

import sys
import struct

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

(SNAKE_RED, SNAKE_BLUE, SNAKE_GREEN, SNAKE_YELLOW) = range(4)
SNAKE_T = {
    SNAKE_RED: 'Red',
    SNAKE_BLUE: 'Blue',
    SNAKE_GREEN: 'Green',
    SNAKE_YELLOW: 'Yellow',
}
SNAKE_CHAR_MAP = {
    'R': SNAKE_RED,
    'G': SNAKE_GREEN,
    'B': SNAKE_BLUE,
    'Y': SNAKE_YELLOW,
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

# Colors.
try:
    import colorama
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
        SNAKE_YELLOW: colorama.Fore.YELLOW,
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
    color_reset = colorama.Style.RESET_ALL
except ModuleNotFoundError:
    color_wall = {
        TYPE_EMPTY: '',
        TYPE_WALL: '',
        TYPE_SPIKE: '',
        TYPE_EXIT: '',
        TYPE_VOID: '',
        TYPE_TELEPORTER: '',
    }
    color_fruit = ''
    color_wall_exit_open = ''
    color_wall_exit_closed = ''
    color_snake = {
        SNAKE_RED: '',
        SNAKE_BLUE: '',
        SNAKE_GREEN: '',
        SNAKE_YELLOW: '',
    }
    color_pushables = [
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
    ]
    color_pushables_decoration = [
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        '',
    ]
    color_reset = ''

class PlayerLose(Exception):
    """
    Custom exception to handle player loss
    """

class Snakebird(object):
    """
    A Snakebird.  Internally this is mostly just a list which has (x,y)
    tuples in it.  Element zero is the head, element -1 is the tail.
    """

    can_exit = True

    def __init__(self, color, level):
        self.color = color
        self.level = level
        self.exited = False
        self.cells = []
        self.checksum_id = bytes(SNAKE_T[self.color][0], encoding='latin1')

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
            dir_to_head = DIR_MODS_REV[(self.cells[i-1][0] - self.cells[i][0],
                self.cells[i-1][1] - self.cells[i][1])]
            if i+1 == len(self):
                dir_to_tail = DIR_REV[dir_to_head]
            else:
                dir_to_tail = DIR_MODS_REV[(self.cells[i+1][0] - self.cells[i][0],
                    self.cells[i+1][1] - self.cells[i][1])]
            self.display_chars.append(SNAKE_CHARS[dir_to_head | dir_to_tail])

    def get_print_char(self, idx):
        """
        Given the passed-in index, return the printing char
        we should use if we're printing out to a console.
        """
        return '{}{}'.format(color_snake[self.color], self.display_chars[idx])

    def move_blindly(self, direction):
        """
        Blindly move us in the specified direction.  Does absolutely no checking on bounds,
        if anything else is in the way, or updating of our level data structures.  Meant
        mostly to be used during push() if we need to undo a recursive string of pushes.
        """
        for idx in range(len(self.cells)):
            self.cells[idx] = (self.cells[idx][0] + DIR_MODS[direction][0],
                self.cells[idx][1] + DIR_MODS[direction][1])

    def push(self, direction, pushing_snake, seen_snakes):
        """
        We were pushed in the specified direction.  Will recursively push anything else
        we're touching, if need be.  `pushing_snake` is the snakebird which initiated
        this push; if we encounter an instance of that snake blocking us, the push will
        fail.  `seen_snakes` should be a set of seen snakes (empty initially, if we're
        the first in the push chain); if we encounter a snake/pushable already in
        `seen_snakes`, we'll skip processing it.
        """

        # Find out what's next to us, in the specified direction, and return False if
        # something's blocking us.
        (snakes, wall, spikes, void, fruit) = self.get_adjacents(direction, pushing_snake=pushing_snake)
        if wall or spikes or void or fruit:
            return (False, None)
        if pushing_snake in snakes:
            return (False, None)

        # At this point we've "seen" ourselves, so make a note of it
        seen_snakes.add(self)

        # Loop through snakes and recursively push
        pushed = set()
        undo_pushes = False
        for sb in snakes:
            if sb not in seen_snakes:
                (was_pushed, ignore) = sb.push(direction, pushing_snake, seen_snakes)
                if was_pushed:
                    pushed.add(sb)
                else:
                    # Need to undo any snakes we may have pushed, thus far
                    undo_pushes = True
                    break
        if undo_pushes:
            for sb in pushed:
                sb.move_blindly(DIR_REV[direction])
            return (False, None)

        # If we got here, we're okay to move.
        self.move_blindly(direction)

        # Finally, if we got here we moved, so return True
        return (True, seen_snakes)

    def process_teleport(self, index, clean_up_level_cells=False):
        """
        Processes a teleport of ourselves, with the teleporter at the given `index`.
        If `clean_up_level_cells` is set to `True`, we will additionally update
        `level.snake_coords` to reflect the new snake position (useful while
        falling)
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

        # Clean up level.snake_coords if told to
        if clean_up_level_cells:
            for coord in self.cells:
                del self.level.snake_coords[coord]
            for coord in new_cells:
                self.level.snake_coords[coord] = self

        # If we got here, we're good to teleport
        self.cells = new_cells
        self.level.teleporter_occupied[cur_pivot] = None
        self.level.teleporter_occupied[new_pivot] = self

        # Return true
        return True

    def move(self, direction):
        """
        Attempts to move us in the specified direction.  Returns `True` if we
        moved, and `False` if we didn't.  Will push other snakebirds/pushables
        out of the way if we can.
        """

        # Grab info about the adjacent cell
        (coords, cell_type) = self.level.get_cell_dir(self.cells[0], direction)

        # First check for snakebirds/pushables, then fruits, and finally map cell type
        do_move = False
        if coords in self.level.snake_coords:
            if self.level.snake_coords[coords] == self:
                return False
            else:
                (pushed, snakes) = self.level.snake_coords[coords].push(direction, self, set())
                if pushed:
                    do_move = True

                    # Look for teleporter entry and exit conditions for all snakes that were
                    # pushed.  We have to wait until now to do this because there's circumstances
                    # where we may have had to undo a push
                    # TODO: I wonder what should happen first - exit or teleport?  Doesn't actually
                    # come into play in the actual levels, though, so difficult to know for sure.
                    for sb in snakes:
                        if not sb.check_exit():
                            teleport_idx = None
                            for (idx, coord) in enumerate(sb.cells):
                                if coord in self.level.teleporter:
                                    teleport_idx = idx
                                    break
                            if teleport_idx is not None:
                                sb.process_teleport(teleport_idx)
                else:
                    return False

        elif coords in self.level.fruits:
            self.level.consume_fruit(coords)
            self.cells.insert(0, coords)
            return True

        elif cell_type == TYPE_EMPTY or cell_type == TYPE_EXIT or cell_type == TYPE_TELEPORTER:
            do_move = True

        # If we got this far, do the actual move.
        if do_move:
            old_coords = self.cells.pop()
            self.cells.insert(0, coords)
            if not self.check_exit():
                if cell_type == TYPE_TELEPORTER:
                    self.process_teleport(0)
            return True
        else:
            return False

    def get_adjacents(self, direction, pushing_snake=None):
        """
        Get a set of items that we're adjacent to (which could
        theoretically be blocking us if we're falling, or prevent
        us from being pushed, etc).  Pass in `pushing_snake` if we're
        being pushed - this is important because if we see a cell
        belonging to `pushing_snake`, it will only actually block if
        it's not the last cell of the snake.

        Returns a tuple of the following:

        (snakes, wall, spikes, void, fruit)

        The first element, `snakes`, is a list of all snakebirds (or
        pushables, actually) that are possibly "supporting" ourself.
        The other three are booleans indicating whether we're up
        against one of `wall`, `spikes`, `void`, or `fruit`

        For snakes being pushed, you'd be blocked by supported OR
        spikes/void.  For snakes falling, spikes/void would mean death unless
        you're also supported.
        """
        # Fruit is always a "platform" even if you're pushing
        # another snake into it; I think the first place you can see
        # that easily is level 26

        snakes = set()
        wall = False
        spikes = False
        void = False
        fruit = False
        for coords in self.cells:
            (other_coords, other_type) = self.level.get_cell_dir(coords, direction)
            if other_coords in self.level.snake_coords:
                if self.level.snake_coords[other_coords] != self:
                    if (pushing_snake is not None and
                            self.level.snake_coords[other_coords] == pushing_snake):
                        if pushing_snake.cells[-1] != other_coords:
                            snakes.add(pushing_snake)
                    else:
                        snakes.add(self.level.snake_coords[other_coords])
            elif other_coords in self.level.fruits:
                fruit = True
            elif other_type == TYPE_WALL:
                wall = True
            elif other_type == TYPE_SPIKE:
                spikes = True
            elif other_type == TYPE_VOID:
                void = True

        # Return!
        return (snakes, wall, spikes, void, fruit)

    def fall(self):
        """
        Fall!  Could potentially be a no-op, of course.  Make sure to keep this
        function in-line with Pushable.fall().

        Returns a tuple containing two booleans:
            * True/False for if we actually fell
            * True/False for if we're supported by a "real" support, as opposed to
              just another snakebird/pushable (useful for the main `check_fall`
              routine to know if it should keep calling us or not)
        """

        if self.exited:
            return (False, True)

        # Find out what's beneath us
        (snakes, wall, spikes, void, fruit) = self.get_adjacents(DIR_D)

        # Convenience vars for our main check_fall loop
        self.fall_supports = snakes
        self.will_destroy_if_fall = (spikes or void)

        # If we have a wall, fruit, or another snake/object under us, we won't fall
        if wall or fruit or len(snakes) > 0:
            return (False, wall or fruit)

        # If we have spikes or void under us, we'll die
        if spikes or void:
            raise PlayerLose('Fell to your death!')

        # Otherwise, we fall!  Woo.  Check for teleport indexes as we go
        teleport_idx = None
        for coord in self.cells:
            del self.level.snake_coords[coord]
        for (idx, c) in enumerate(self.cells.copy()):
            self.cells[idx] = (c[0] + DIR_MODS[DIR_D][0], c[1] + DIR_MODS[DIR_D][1])
            self.level.snake_coords[self.cells[idx]] = self
            if self.cells[idx] in self.level.teleporter:
                teleport_idx = idx

        # TODO: I wonder what would happen first - exit or teleport?

        # Check to see if we exited - this can happen in the middle
        # of a fall (I think level 4 is the first where we can
        # conclusively say this)
        if not self.check_exit(clean_up_level_cells=True):
            # If we were pushed into a teleporter, take care of that.
            if teleport_idx is not None:
                self.process_teleport(teleport_idx, clean_up_level_cells=True)

        # Alas, calling out to update our teleporter_occupied struct
        self.level.populate_teleporter_coords()

        # We fell, so return true
        return (True, False)

    def check_exit(self, clean_up_level_cells=False):
        """
        Check to see if our Snakebird has exited, and if so, handle it.  Returns
        `True` if we did, and `False` otherwise.  Will call `level.check_win()`
        if we did, to see if we've won or not.  If the optional argument
        `clean_up_level_cells` is set to `True`, we will clear out this Snakebird's
        entries in `level.snake_coords`.
        """
        if (self.can_exit and
                self.level.cells[self.cells[0][1]][self.cells[0][0]] == TYPE_EXIT and
                len(self.level.fruits) == 0):
            if clean_up_level_cells:
                for coord in self.cells:
                    del self.level.snake_coords[coord]
            self.exited = True
            self.cells = []
            self.level.check_win()
            return True
        else:
            return False

    def destroy(self):
        """
        Destroys ourself (just raises an exception)
        """
        raise PlayerLose('Fell to your death!')

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
        return b''.join([struct.pack('BB', *c) for c in self.cells])

class Pushable(Snakebird):
    """
    A pushable object.  We're subclassing Snakebird because there's
    enough in common (specifically get_adjancents() and push()) which
    we'd otherwise have to just copy+paste into here.
    """

    can_exit = False

    def __init__(self, desc, level):
        self.desc = desc
        self.level = level
        self.cells = []
        self.cells_decoration = []
        self.checksum_id = struct.pack('B', desc)

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
                    color_reset,
                )
        return ret_dict

    def fall(self):
        """
        Fall!  Could potentially be a no-op, of course.  Make sure to keep this
        function in-line with Snakebird.fall().

        Returns a tuple containing two booleans:
            * True/False for if we actually fell.  (We'll return `True` if we were
              destroyed by a void tile.)
            * True/False for if we're supported by a "real" support, as opposed to
              just another snakebird/pushable (useful for the main `check_fall`
              routine to know if it should keep calling us or not)
        """

        if len(self.cells) == 0:
            return (False, True)

        # Find out what's beneath us
        (snakes, wall, spikes, void, fruit) = self.get_adjacents(DIR_D)

        # Convenience vars for our main check_fall loop
        self.fall_supports = snakes
        self.will_destroy_if_fall = void

        # If we have a wall, fruit, spikes, or another snake/object under us, we won't fall
        if wall or fruit or spikes or len(snakes) > 0:
            return (False, wall or fruit or spikes)

        # If we have void under us, we'll technically fall, but also disappear,
        # maybe causing a lose condition.
        if void:
            self.destroy()
            # The second boolean is technically incorrect, but will prevent us
            # from being called again from the main check_fall loop.
            return (True, True)

        # Otherwise, we fall!  Woo.  Check for teleport indexes as we go
        teleport_idx = None
        for coord in self.cells:
            del self.level.snake_coords[coord]
        for (idx, c) in enumerate(self.cells.copy()):
            self.cells[idx] = (c[0] + DIR_MODS[DIR_D][0], c[1] + DIR_MODS[DIR_D][1])
            self.level.snake_coords[self.cells[idx]] = self
            if self.cells[idx] in self.level.teleporter:
                teleport_idx = idx

        # If we were pushed into a teleporter, take care of that.
        if teleport_idx is not None:
            self.process_teleport(teleport_idx, clean_up_level_cells=True)

        # We fell, so return true
        return (True, False)

    def destroy(self):
        """
        Destroys ourself (ie: we fell into void)
        """
        self.cells = []
        if self.level.die_on_pushable_loss:
            raise PlayerLose('Lost a pushable object!')

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
            return b''
        else:
            return struct.pack('BB', *self.cells[0])

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
                        if color in self.snakebirds:
                            raise Exception('ERROR: Snakebird {} defined twice.'.format(str(self.snakebirds[color])))
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
        for sb in self.snakebirds_l:
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

        # Make sure we have an exit!
        if not have_exit:
            raise Exception('No exit defined in file!')

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

        # Also do teleporters, but in a separate function
        self.populate_teleporter_coords()


    def populate_teleporter_coords(self):
        """
        Make sure our `teleporter_occupied` info is correct
        """
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
        new_x = coords[0] + DIR_MODS[direction][0]
        new_y = coords[1] + DIR_MODS[direction][1]
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
        something_fell = True
        to_process = set(self.interactives)
        supported_objs = set()
        while something_fell:
            something_fell = False
            for sb in to_process.copy():
                (fell, supported) = sb.fall()
                if fell:
                    something_fell = True
                elif supported:
                    to_process.remove(sb)
                    supported_objs.add(sb)

            # If nothing fell but we have objects left in to_process,
            # we've got objects supported by other objects.  The supporting
            # objects will either be supported themselves (in which case we
            # can do nothing), but the other alternative is that we've got
            # a more complex situation where objects appear to be supporting
            # each other, such as:
            #
            #       ╔═   
            #       ║G══ 
            #       ╚R   
            #
            # Or, with a disjoint pushable object:
            #
            #         ▰    
            #         B    
            #       ▰─║─▰  
            #         ║    
            #         ▰    
            #
            # So, recursion of a sort needs to happen.

            if not something_fell and len(to_process) > 0:
                set_supported_obj = True
                while set_supported_obj and len(to_process) > 0:
                    set_supported_obj = False
                    for sb in to_process.copy():
                        if sb not in supported_objs:
                            for sb_support in sb.fall_supports:
                                if sb_support in supported_objs:
                                    supported_objs.add(sb)
                                    to_process.remove(sb)
                                    set_supported_obj = True
                                    break

                # If we get here, anything left in to_process should
                # fall as a group
                if len(to_process) > 0:
                    for sb in to_process.copy():
                        for coord in sb.cells:
                            del self.snake_coords[coord]
                        if sb.will_destroy_if_fall:
                            sb.destroy()
                            to_process.remove(sb)
                    for sb in to_process:
                        teleport_idx = None
                        for (idx, c) in enumerate(sb.cells.copy()):
                            sb.cells[idx] = (c[0] + DIR_MODS[DIR_D][0], c[1] + DIR_MODS[DIR_D][1])
                            self.snake_coords[sb.cells[idx]] = sb
                            if sb.cells[idx] in self.teleporter:
                                teleport_idx = idx
                        if not sb.check_exit(clean_up_level_cells=True):
                            if teleport_idx is not None:
                                sb.process_teleport(teleport_idx, clean_up_level_cells=True)

                    # ... aaand note that we fell.
                    something_fell = True

            # If we won, return!
            if self.won:
                return True

        return False

    def print_level(self):
        """
        Prints out our level
        """

        # First grab information about our snakes
        disp_snake_coords = {}
        for sb in self.snakebirds_l:
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
                        color_reset,
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
            sys.stdout.write("{}\n".format(color_reset));

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
        self.snakebirds_l = []
        self.pushables = {}
        self.moves = moves
        self.teleporter_occupied = level.teleporter_occupied.copy()

        for coord in level.fruits.keys():
            self.fruits[coord] = True
        # TODO: I feel these could be combined...
        for sb in level.snakebirds_l:
            self.snakebirds_l.append(sb.clone())
        for (num, obj) in level.pushables.items():
            self.pushables[num] = obj.clone()

    def apply(self):

        self.level.fruits = {}
        for coords in self.fruits.keys():
            self.level.fruits[coords] = True

        for sb in self.snakebirds_l:
            self.level.snakebirds[sb.color].apply_clone(sb)

        for num in self.pushables.keys():
            self.level.pushables[num].apply_clone(self.pushables[num])

        self.level.populate_snake_coords()

        self.level.teleporter_occupied = self.teleporter_occupied.copy()

        if self.moves is not None:
            return list(self.moves)

    def checksum(self):
        """
        Construct a "checksum" of our state so we can compare to see if we
        have a loop while solving (to prune off the possibility tree).
        Really this is more than a checksum, since it could theoretically
        be used to save/restore gamestate in general.

        The original version of this, from 2017 or so, was a basically human-
        readable string.  In March 2019 I converted to a binary format (using
        struct.pack()) which is rather more memory-efficient, and lets our
        unsolveable puzzles get at least further along before I have to kill
        it for excessive memory usage (though not by enough to make any
        previously-unsolveable puzzles solveable).  A more noticeable bonus
        is that it looks like this binary method is faster than the string
        version, which makes sense in retrospect.
        """

        sumlist = []

        # Teleporter (just need to know if it's occupied or not)
        # TODO: Though looking back on this in 2019: why exactly
        # does this matter in terms of checksums?  Wouldn't this be
        # implied by snakebird/pushable coords?  It makes sense that
        # it's a useful bit of information to store in the object,
        # but even if we were using these checksums as "real" save
        # states, we'd theoretically be able to populate it on "load"
        # based on the sb/push coords, yeah?
        tp_list = []
        if len(self.level.teleporter) > 0:
            for (idx, (coord, occupier)) in enumerate(self.level.teleporter_occupied.items()):
                if occupier is None:
                    tp_list.append(b'\xfe')
                else:
                    tp_list.append(occupier.checksum_id)
        sumlist.append(b''.join(tp_list))

        # Fruit
        sumlist.append(b''.join([struct.pack('BB', *fruit) for fruit in self.fruits.keys()]))

        # TODO: Ditto re: combination
        # ^ I assume this refers to the note in State.__init__ but heck if
        # I remember what I was on about, back then.

        # Old snakebird checksum:
        #for sb in self.snakebirds_l:
        #    sumlist.append('s-{}={}'.format(sb.color, sb.checksum()))

        # New snakebird checksum - snakebirds of the same length are
        # considered interchangeable, basically.  If two snakebirds
        # of the same length swap positions entirely, there's no logical
        # difference between that and the original ordering.  This cuts
        # down on the probability space for some multi-snakebird levels,
        # and noticeably improves solve times for a handful of those,
        # though it doesn't do so sufficiently to let us solve any levels
        # which were exhausting memory previously.  It's possible the
        # sorting in here will actually increase solve times for some
        # levels, though from my testing that's pretty negligible if
        # it does happen.
        sumlist.extend(sorted([sb.checksum() for sb in self.snakebirds_l]))

        # Pushables
        sumlist.append(b''.join([obj.checksum() for obj in self.pushables.values()]))

        # Construct the full checksum
        return b'\xff'.join(sumlist)

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
        """
        Move the snakebird in the given direction - if the
        snake moves properly, advance our state.
        """
        self.moves.append((sb, direction))
        self.push_state(state)
        self.cur_steps += 1
        if (sb.move(direction)):
            self.level.populate_snake_coords()
            # Check to see if we won and exit if we have
            if self.level.won:
                return True
            self.level.check_fall()
            return self.level.won

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
                color_reset,
            ))

    def interactive(self):
        import readchar
        colorama.init(autoreset=True)
        while True:
            self.cur_snakebird = self.level.snakebirds_l[self.cur_snakebird_idx]
            if not self.level.won and self.alive:
                while self.cur_snakebird.exited == True:
                    self.cur_snakebird_idx = ((self.cur_snakebird_idx + 1) % len(self.level.snakebirds))
                    self.cur_snakebird = self.level.snakebirds_l[self.cur_snakebird_idx]
            self.print_status()
            full_control = True
            if self.level.won:
                return True
            elif self.alive == False:
                full_control = False

            # Whether to show full movement controls
            if full_control:
                if len(self.level.snakebirds) > 1:
                    ctrl_str = '[wasd] - movement, [tab/c]hange snakebirds, '
                else:
                    ctrl_str = '[wasd] - movement, '
            else:
                ctrl_str = ''

            # Whether or not to enable undo command
            if len(self.states) > 0:
                undo_str = '[u]ndo, '
            else:
                undo_str = ''

            # Show options
            print('{}{}[r]eset, [q]uit, [i]nfo'.format(ctrl_str, undo_str))
            sys.stdout.write('[{}] > '.format(self.cur_steps + 1))
            sys.stdout.flush()

            valid_input = False
            while not valid_input:
                cmd = readchar.readchar().lower()
                if cmd == "\t":
                    report = '[tab]'
                else:
                    report = cmd

                direction = None
                if cmd == 'q':
                    print(report)
                    return False
                elif cmd == 'u':
                    valid_input = True
                    self.undo()
                elif cmd == 'r':
                    while len(self.states) > 0:
                        valid_input = True
                        self.undo()
                elif cmd == 'i':
                    valid_input = True
                    self.print_debug_info()
                elif full_control and len(self.level.snakebirds) > 1 and (cmd == 'c' or cmd == "\t"):
                    valid_input = True
                    self.cur_snakebird_idx = ((self.cur_snakebird_idx + 1) % len(self.level.snakebirds))
                    while self.level.snakebirds_l[self.cur_snakebird_idx].exited == True:
                        self.cur_snakebird_idx = ((self.cur_snakebird_idx + 1) % len(self.level.snakebirds))
                elif full_control and cmd in DIR_CMD:
                    valid_input = True
                    direction = DIR_CMD[cmd]
                    try:
                        self.move(self.cur_snakebird, DIR_CMD[cmd])
                    except PlayerLose as e:
                        self.alive = False
                        report_str = 'Player Death: {}'.format(e)
                        print('-'*len(report_str))
                        print(report_str)
                        print('-'*len(report_str))
                    except Exception as e:
                        print('Got exception!')
                        self.print_debug_info()
                        raise e

                if valid_input:
                    print(report)

    def solve_recurs(self, quiet=False):
        """
        Recursive depth-first solver algorithm.  In most cases, especially
        levels with a single snakebird, the breadth-first search (below)
        is faster, though sometimes this one happens to win out, probably
        just due to luck.

        Unless a level has `return_first_solution` defined, we'll continue
        to refine solutions until we've found the shortest one.  (Though
        of course a level may have more than one solution with the same
        number of moves.
        """

        if self.level.return_first_solution and self.solution is not None:
            return
        (state, new_checksum) = self.get_state()
        if not new_checksum:
            return
        for sb in self.level.snakebirds_l:
            if not sb.exited:
                for direction in DIRS:
                    try:
                        self.move(sb, direction, state)
                        if self.level.won:
                            self.store_winning_moves(quiet=quiet, display_moves=False)
                            if self.level.return_first_solution:
                                return
                            self.undo()
                        else:
                            if self.step_limit():
                                self.undo()
                            else:
                                self.solve_recurs(quiet=quiet)
                                self.undo()
                    except PlayerLose:
                        self.undo()

    def solve_bfs(self, quiet=False):
        """
        Our attempt at a breadth-first solver, inspired on
        https://github.com/david-westreicher/snakebird

        Note that that solver is probably faster than ours in general 'cause
        it's not so bogged down by spurious classes, etc.  I suspect its
        overall implementation is more efficient in all sorts of ways.  Ah
        well!

        In most cases, this is going to be faster than our original recursive
        (DFS) implementation.  It still runs into problems with multi-snake
        puzzles (as does David Westreicher's version) when the step count is
        high and there's not enough death situations to trim the tree down.

        Occasionally our original method is quicker, though.

        By definition, a solution found here will be the shortest one
        available, though a level could have multiple solutions with the same
        length.
        """
        queue = [self.get_state(self.moves)[0]]
        for i in range(self.max_steps):
            next_queue = []
            if not quiet:
                sys.stdout.write("\rAt depth: {}...".format(i))
                sys.stdout.flush()
            for state in queue:
                self.moves = state.apply()
                for sb in self.level.snakebirds_l:
                    if not sb.exited:
                        for direction in DIRS:
                            self.moves = state.apply()
                            try:
                                self.move(sb, direction, state)
                                if self.level.won:
                                    if not quiet:
                                        print('')
                                    self.store_winning_moves(quiet=quiet, display_moves=False)
                                    return
                                (new_state, is_new_state) = self.get_state(self.moves)
                                if is_new_state:
                                    next_queue.append(new_state)
                            except PlayerLose:
                                pass
            queue = next_queue
            if len(next_queue) == 0:
                break
        if not quiet:
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
