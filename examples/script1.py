#!/usr/bin/env python

import os

# Read from one file.
data = open('file1.txt').read()

# Output to another.
with open('file2.txt', 'w') as out:
    out.write('Write to file2.')

# Make a subprocess.
os.system('ls')
