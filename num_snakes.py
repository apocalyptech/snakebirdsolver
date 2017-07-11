#!/usr/bin/env python
# vim: set expandtab tabstop=4 shiftwidth=4:

import os

files = sorted(os.listdir('.'))
for filename in files:
    if filename[:5] == 'level' and filename[-4:] == '.txt':
        with open(filename, 'r') as df:
            num_snakes = 0
            for line in df.readlines():
                if 'R' in line:
                    num_snakes += 1
                if 'G' in line:
                    num_snakes += 1
                if 'B' in line:
                    num_snakes += 1
            print('{}: {}'.format(filename, num_snakes))
