#!/usr/bin/env pypy3
# vim: set expandtab tabstop=4 shiftwidth=4:

import os
import sys
import signal
import argparse
from snakebirdsolver.app import Level, Game, DIR_U, DIR_D, DIR_L, DIR_R, DIR_T, SNAKE_T

game = None

def report_game_end():
    global game
    if game.solution is None:
        if game.max_steps is None:
            print('No solutions found!')
        else:
            print('No solutions found in %d turns!' % (game.max_steps))
    else:
        game.print_winning_move_set(game.solution)
    #for csum in sorted(game.checksums.keys()):
    #    print(csum)
    sys.exit(0)

def ctrl_c_handler(signal, frame):
    print('')
    print('')
    print('Ctrl-C detected; showing best result so far')
    print('(Unlikely to be optimal!)')
    print('')
    report_game_end()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Play or solve Snakebird levels',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    group = parser.add_mutually_exclusive_group()

    group.add_argument('-i', '--interactive',
        action='store_true',
        help='Run interactively rather than in solver mode')

    group.add_argument('-t', '--test',
        action='store_true',
        help='Generate python code suitable for a unit test')

    parser.add_argument('-l', '--level',
        required=True,
        metavar='FILENAME',
        help='Level file to run')

    parser.add_argument('-a', '--algorithm',
        choices=('BFS', 'DFS'),
        help='Algorithm to use: Breadth-First Search or Depth-First Search')

    args = parser.parse_args()

    if not os.path.exists(args.level):
        print('Error: {} does not exist'.format(args.level))
        sys.exit(1)

    game = Game(args.level)

    if args.algorithm:
        game.level.preferred_algorithm = args.algorithm

    if args.interactive:
        game.interactive()
#    elif args.test:
#        dir_str = {
#            DIR_U: 'DIR_U',
#            DIR_D: 'DIR_D',
#            DIR_R: 'DIR_R',
#            DIR_L: 'DIR_L',
#        }
#        game.solve()
#        if game.solution is None:
#            if game.max_steps is None:
#                print('No solutions found!')
#            else:
#                print('No solutions found in %d turns!' % (game.max_steps))
#        else:
#            print('')
#            print('    def test_%s(self):' % (args.level))
#            print('        game = Game(\'%s\')' % (args.level))
#            print('        game.solve()')
#            print('        self.assertEqual(game.solution, [')
#            for direction in game.solution:
#                print('            %s,' % (dir_str[direction]))
#            print('        ])')
#            print('')
    else:

        if game.level.preferred_algorithm == 'DFS':
            print('Using depth-first search algorithm')
            print('Solving {} - Maximum Steps: {}'.format(game.level.desc, game.level.max_defined_steps))
            if game.level.return_first_solution:
                print('NOTE: Will return the first solution found, not the shortest one.')
            print('')
            print('Ctrl-C to break out of solver loop and display most recent solution.')
            print('(Notification will be printed as solutions are found)')
            print('')
            signal.signal(signal.SIGINT, ctrl_c_handler)
            try:
                game.solve_recurs()
            except Exception as e:
                game.print_debug_info(e)
                raise e

        elif game.level.preferred_algorithm == 'BFS':
            print('Using breadth-first search algorithm')
            print('Solving {} - Maximum Depth: {}'.format(game.level.desc, game.level.max_defined_steps))
            print('')
            try:
                game.solve_bfs()
            except Exception as e:
                game.print_debug_info(e)
                raise e

        else:
            raise Exception('Unknown preferred algorithm!')
        report_game_end()
