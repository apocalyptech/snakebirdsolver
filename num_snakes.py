#!/usr/bin/env python
# vim: set expandtab tabstop=4 shiftwidth=4:

import os

files = sorted(os.listdir('.'))
for filename in files:
    if ((filename.startswith('level') or filename.startswith('primer')) and
            filename.endswith('.txt')):
        with open(filename, 'r') as df:
            num_snakes = 0
            seen_level = False
            objects = set()
            teleporter = False
            for line in df.readlines():
                if seen_level:
                    if 'R' in line:
                        num_snakes += 1
                    if 'G' in line:
                        num_snakes += 1
                    if 'B' in line:
                        num_snakes += 1
                    if 'Y' in line:
                        num_snakes += 1
                    if '0' in line:
                        objects.add('0')
                    if '1' in line:
                        objects.add('1')
                    if '2' in line:
                        objects.add('2')
                    if '3' in line:
                        objects.add('3')
                    if '4' in line:
                        objects.add('4')
                    if '5' in line:
                        objects.add('5')
                    if '6' in line:
                        objects.add('6')
                    if '7' in line:
                        objects.add('7')
                    if '8' in line:
                        objects.add('8')
                    if '9' in line:
                        objects.add('9')
                    if 'T' in line:
                        teleporter = True
                if line.lower().startswith('level: '):
                    seen_level = True
            print('{}: {} snakes, {} pushables, teleporter: {}'.format(
                filename,
                num_snakes,
                len(objects),
                teleporter,
                ))
