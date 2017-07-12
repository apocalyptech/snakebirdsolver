Snakebird Bruteforce Solver
===========================

This is a bruteforce solver for the excellent puzzle game Snakebird,
by Noumenon Games.

http://snakebird.noumenongames.com/
http://store.steampowered.com/app/357300/Snakebird/

![Interactive Mode](sb_interactive.png) ![Auto-Solver](sb_solve.png)

It's often quite slow.  Puzzles with more than one snakebird, long
snakebirds, or multiple pushable objects will often go into the tens
of minutes, or even hours to solve.  Some I've not let run to
completion.  The game in general doesn't really lend itself to
bruteforce solving; there's just too many moving parts, and the
possible action tree is ridiculously wide and deep.  Even simple
levels can end up taking a minute or two to solve, even when using
PyPy3.

The game uses either of two algorithms to find solutions:
breadth-first (the default) or depth-first.  Puzzles which are known
to work better with Depth-First are configured to default to that
one instead (currently we have just one of those).  The Breadth-First
attempt was inspired by another Snakebird solver:
https://github.com/david-westreicher/snakebird - That version is
rather more efficient than mine in nearly all respects, though
suffers from much the same exponential-choice performance problems as
mine once the snakebird count goes up and the solutions get longer.

Note that Breadth-First Searching can get pretty memory intensive if
the tree is wide and deep enough, since we've got to keep track of
game state along each path.  I'd let one level solve attempt go
overnight and came back to a badly-swapping system.  Depth-First
should be much kinder to system memory, and could theoretically be
run for quite a bit longer, but it is in general slower than BFS.

There's plenty in the code that could be optimized - I'm sure we're
doing unnecessary calculations all the time, or needlessly
complicating things with class abstraction, etc.  The other solver
mentioned above is much better in that regard.  On a higher level, I
suspect that going back to spend some time on actual CS theory and
algorithm construction could help, and there are probably several math
concepts which could help find shortcuts.

There are some tests in `tests.py` which just check the solver against
known-good solutions for some of the more-quickly-solved puzzles.  Not
actual unit tests, alas, but slightly better than nothing.

Usage
=====

Theoretically runnable with any Python 3 (and probably Python 2),
though it more or less requires PyPy3/PyPy.  Processing is slow
enough with PyPy3 that I can't imagine running it in CPython.

The `colorama` Python module is required for some output colorization
when running interactively, and the `numpy` module is used to do
some tuple arithmetic.

To solve a level:

    ./solve.py -l level1.txt

To solve a level with either DFS or BFS:

    ./solve.py -l level1.txt -a DFS
    ./solve.py -l level1.txt -a BFS

To run interactively:

    ./solve.py -l level1.txt -i

To get help on the commandline args (though there's really only
what I just mentioned):

    ./solve.py -h

Interactive mode uses `wasd` for navigation, `c` to change between
Snakebirds, `u` to undo, `r` to reset, and `q` to quit.  Not the
best way to play the game, really - I mostly use it just to test
out the app.

Level Definition
================

All Snakebird levels are included here, but for reference, here's
what the level definition files look like.  The level definition
files are just plaintext, and start off with a few directives at the
top.  The directives are case-insensitive.

    Alg: DFS
    Alg: BFS

Set Depth-First Search as the default algorithm for this level, or
Breadth-First Search (though BFS is the default, so there's not really
much point in specifying it).

    ExitOnFirst

This one only has an effect while using Depth-First Search, and will
cause the algorithm to exit when the first solution is found, rather
than trying to refine and find a shorter solution.

    AllowPushableLoss

By default, if a pushable object is knocked off the edge (to fall into
the water or whatever), the solver will consider that a losing
condition, even though that doesn't actually match what Snakebird
does.  Since the vast majority of levels require that all objects
remain in play, though, we do this to help improve solve times.  One
level does require that an object be sacrificed, though.

    Max: <number>

Specifies the maximum number of steps to compute.  This is most useful
for Depth-First Search, to limit the tree size, though technically it
also applies to Breadth-First as well.

    Decoration <num>: <number of lines>

This directive specifies some optional "decorations" which are drawn
on pushable objects - for instance, the ones which look like a plus
sign or dumbbells.  The "connective tissue," so to speak, of those
objects doesn't actually interact with the map at all, but it's kind
of nice to have drawn on the map when playing interactively, so
that's what this is for.  This directive is followed immediately by
the number of lines specified after the colon, and uses the letter
'O' to specify the "real" cells (only the very first one is
required, actually - the rest are ignored), and the decorations are
specified with a combination of pipes, dashes, and plus signs (`|`,
`-`, and `+`).  For instance, in Level 25:

	Decoration 0: 5
	  O
	  |
	O-+-O
	  |
	  O

The first number should match the number used in the level definition.

	Level: <identifier>

This indicates that the remainder of the file contains level data.
Some empty-space padding will automatically be added along the edges,
along with a border composed of "void" cells.  The level definition
need not have a fixed width or anything; it'll be sized appropriately
as the level is read.

The following characters are used:

* `~` - "Void", generally water at the bottom.  The solver will
  automatically add a border of Void around the level.
* `w` - Walls
* `%` - Spikes
* `F` - Fruit
* `E` - Exit
* `T` - Teleporter *(exactly two are required, if using teleporters)*
* `R`/`G`/`B` - Snakebird Heads
* `<`/`^`/`>`/`V` - Snakebird Bodies - should point towards the head.
  For instance, `G<<<` would indicate a green snakebird of length
  four, all pointing towards the left.
* `0`-`9` - Pushable objects.  These can be geographically diverse,
  and will all move as one in terms of pushing and falling, etc.  If
  you want connective decorations to be drawn between the cells of an
  object, see the `Decoration` tag at the start of the file.  You
  don't have to specify these in numerical order; mix and match if you
  like.

Performance
===========

As I say, it's often bad, and gets exponentially worse when there's more
than one Snakebird or pushable object in play.  So far I've not gotten 
it to solve any of the three-snakebird levels, for instance, and level
42 (with four pushables) got to nearly eight hours on a by-then badly
swapping system before I cancelled it.

A few levels benefit from specifying a maximum move count when using
the depth-first search algorithm, even though Snakebird itself doesn't
have such a concept.  It helps keep the tree down to a
computationally-feasible size.  Level 11, for instance, takes a super
long time unless you specify as small a max-steps as possible.  Even
increasing from 35 to 40 makes the solve time take forever.  However,
**with** a max step of 35, it ends up beating out the breadth-first
algorithm.  Go figure.  So, for some of these I've set a max move
count, knowing what the solutions already are, just to save on
processing time.  There's a default max move limit of 100, if one
isn't specified in the level file - a few levels come close to that
limit (and the solution to Star 4 is something like 140 steps long),
though in general those levels are a bit too slow to solve with this
anyway.

By default, the game will consider the loss of any pushable object to
be a game loss, even though the real game allows it.  This is done to
help trim the solving tree down a bit, since in general solutions
require all the objects to be in place.  This can be overridden on a
per-level basis with the "AllowPushableLoss" directive.

Comparison
==========

As mentioned far above, there's another bruteforce Snakebird solver on
github, at: https://github.com/david-westreicher/snakebird

Things David Westreicher's solver does better:

 * Is noticeably faster
 * Outputs its found moves in a nice condensed format ("3x Right").  Its
   move-testing order, relatedly, makes it more likely that you'll stick
   with moving a specific snakebird as long as possible, rather than
   going back and forth, which can happen with mine.
 * Apparently supports reading Snakebird level data from screenshots,
   though I hadn't tested that out myself.
 * Also apparently can send keystrokes directly to a running Snakebird
   process, to solve a level in-game.  I hadn't tested that out,
   either.  (Relatedly, its solution output matches what you'd have to
   give to Snakebird, including "change snakebird" keys.)

Things my solver does better:

 * Supports pushable objects
 * Supports teleporters
 * A bit more flexible with regards to initial snakebird placement - I
   think the other one is pretty picky about how snakebirds are placed
   in the level definition files
 * We've got a complete set of Snakebird level files to play with; the
   other one only includes the first five

Bugs
====

* The code is, in general, quite inefficient, and could be optimized
  in a number of ways.

Current Solve Times
===================

Obviously this depends greatly on CPU, though the comparative times
should still apply regardless.  I'm using a pretty ancient AMD
A8-6500.  These are all just single data points - it's possible that
other CPU load could've affected my numbers here.  Note that the app
is single-threaded and will only operate on a single core.

Also note that when processing with DFS, the levels with multiple
snakebirds randomize which moves are made first, so solve times can
vary depending on how lucky the PRNG is, and the solution you get may
not necessarily be the same from run to run.

Times are in *M:SS*.  An "(L)" in the DFS column indicates that we're
limiting the step count to improve time - without specifying that in
the file, the DFS time will be longer, sometimes very significantly
so.  An "(L+)" means that the step count we're specifying in the level
is actually set to the optimal solution length itself, so that's about
as quick as DFS will get.  The better time of the two is noted with
**bold text**.

I haven't tried many of the levels on DFS after implementing BFS, since
it turned out BFS was in general so much more effective.  If an entry
here is blank, it means that I've not even attempted solving the level
with the given algorithm.  If I've tried but cancelled after it was
clear it was going to take way too long, I've noted the cancellation
time.

Single Snakebird Levels
-----------------------

| Level         | Moves | BFS       | DFS           | Notes |
| ------------- | ----- | --------- | ------------- | ----- |
| **Level 0**   | 29    | **0:05**  | 1:06 (L)      |       |
| **Level 1**   | 16    | **0:02**  | 0:02          |       |
| **Level 2**   | 25    | **0:03**  | 0:33          |       |
| **Level 3**   | 27    | **0:03**  | 0:46          |       |
| **Level 4**   | 30    | **0:03**  | 0:16          |       |
| **Level 5**   | 24    | **0:02**  | 0:09          |       |
| **Level 6**   | 36    | **0:02**  | 0:21          |       |
| **Level 10**  | 33    | **0:08**  | 3:04          |       |
| **Level 11**  | 35    | 47:25     | **0:02** (L+) | *It's luck, effectively, that DFS is so much better* |
| **Level 12**  | 52    | **0:13**  | 3:34 (L)      |       |
| **Level 21**  | 39    | **0:19**  | 3:18 (L+)     |       |
| **Level 22**  | 45    | **0:05**  | 1:01 (L)      | One Pushable |
| **Level 23**  |       | *(cancelled at 80min)* |  | Two Pushables |
| **Level 24**  | 26    | 14:24     |               | One Pushable |
| **Level 30**  | 15    | 0:02      |               | Teleporter |
| **Level 31**  | 8     | 0:02      |               | Teleporter |
| **Level 33**  | 42    | 0:03      |               | Teleporter |
| **Level 35**  | 29    | 0:04      |               | Teleporter |
| **Level 39**  | 57    | 3:58      |               | Two Pushables |
| **Star 2**    | 60    | 1:06      |               |       |

Two-Snakebird Levels
--------------------

| Level         | Moves | BFS       | DFS           | Notes |
| ------------- | ----- | --------- | ------------- | ----- |
| **Level 7**   | 43    | **8:23**  | *(cancelled at some point)* | |
| **Level 8**   | 29    | **13:28** | *(cancelled at 2 hours)* | |
| **Level 9**   | 37    | 80:03     |               |       |
| **Level 13**  | 44    | **19:23** | *(cancelled at some point)* | |
| **Level 14**  | 24    | **0:07**  | 0:55          |       |
| **Level 15**  | 34    | **18:30** | *(cancelled at 20min)* | |
| **Level 17**  | 69    | **3:35**  | *(cancelled at 20min)* | |
| **Level 18**  | 35    | **2:08**  | *(cancelled at 10min)* | |
| **Level 20**  | 50    | **0:47**  | 4:46 (L+)     |       |
| **Level 25**  |       | *(cancelled at 90min)* |  | One Pushable |
| **Level 26**  | 35    | 3:02      |               | One Pushable |
| **Level 27**  | 49    | 10:55     |               | One Pushable |
| **Level 28**  | 49    | 52:40     |               | Two Pushables |
| **Level 29**  |       | *(cancelled at 7.5hrs)* | | Four Pushables |
| **Level 32**  | 21    | 0:13      |               | One Pushable, Teleporter |
| **Level 34**  | 17    | 0:22      |               | One Pushable, Teleporter |
| **Level 36**  | 29    | 10:03     |               | Teleporter |
| **Level 37**  | 16    | 0:20      |               | Teleporter |
| **Level 38**  | 28    | 16:29     |               | Teleporter |
| **Level 40**  |       | *(cancelled at 2.75hrs)* | | Two Pushables |
| **Level 41**  | 34    | **6:29**  | 58:55 (L+)    |       |
| **Level 42**  | 42    | **0:56**  | 6:02 (L+)     |       |
| **Level 43**  | 36    | 2:25      |               | One Pushable, requires `AllowPushableLoss` |
| **Level 44**  | 36    | 1:14      |               | Teleporter |
| **Level 45**  |       | *(cancelled at 2hrs)* |   | Two Pushables |
| **Star 4**    |       | *(cancelled at 90min)* |  | Three Pushables |
| **Star 5**    |       | *(cancelled at 90min)* |  | One Pushable, Teleporter |

Three-Snakebird Levels
----------------------

| Level           | Moves | BFS       | DFS           | Notes |
| --------------- | ----- | --------- | ------------- | ----- |
| **Level 16**    |       | *(cancelled at 2.5 hours)* |               |       |
| **Level 19**    |       | *(cancelled at 2 hours)* |           |       |
| **Star 1**      |       |           |               | One Pushable |
| **Star 3**      |       |           |               | One Pushable |
| **Star 6**      |       |           |               | Three Pushables |
| **??? (Space)** |       |           |               | One Pushable |
