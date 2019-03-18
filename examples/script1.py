#!/usr/bin/env python

import os

# Read from one file.
this_dir = os.path.dirname(__file__)
data = open(os.path.join(this_dir, 'file1.txt')).read()

# Output to another.
with open(os.path.join(this_dir, 'file2.txt'), 'w') as out:
    out.write('Write to file2.')

# Make a subprocess.
os.system('ls')
