# Tot: Total Recall program tracing tool

*tot* is a unix tool for logging process execution and file IO. It uses kernel
tracing and virtual file systems to detect every process fork and file IO operation. These logs
can then be imported into a database and analyzed.

Currently, this repo contains an experimental prototype of how such a command could work.
I originally started this experiment as Christmas break project in 2015.

## Example

```
# Log a command: python example/script1.py
tot log python examples/script1.py

# Import the logs tot.log and tot-fs.log
tot import tot.log tot-fs.log

# Display the logged executions.
tot show
```

## Getting started

To try out the prototype and run the unit tests we first need to setup
the dev environment.

Running the examples requires Vagrant. Start the vagrant virtual machine:

```sh
vagrant up
```

Log into the VM with:

```sh
vagrant ssh
```

Change into the code directory mounted at `/vagrant` and install the
dependencies within the VM.

```sh
cd /vagrant
make setup
```

To verify everything is working correctly, run the tests:

```sh
make test
```

### Log your first command

Let's look at an example program [script1.py](examples/script1.py). It should look something
like this:

```py
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
```

We can run the python program using:

```sh
examples/script1.py
```

To log the command, we simply prepend `tot`.

```sh
bin/tot log examples/script1.py
```

The program will run as before, however two log files will be created:
- `tot.log`: A JSON-formatted log of the major syscalls that `script1.py` made.
- `tot-fs.log`: A JSON-formatted log of the file input and output that `script1.py` performed.

These are the default file paths. They can be explicitly specified with `--log` and `--log-fs`.

To make searching these log files more efficient, we can import them into a sqlite database.
Currently in this prototype, this is not done automatically, but could be implemented if desired:

```sh
bin/tot import tot.log tot-fs.log
```

On the first run, this will create a sqlite database `tot.db`. Similarly, a different file path
can be specified with `--db`.

We can now query and display the log commands and their syscalls and IO using

```sh
bin/tot show
```

Which should display something like the following:

```
2019-32-17 23:32:49 0ec9e154 $ examples/script1.py
  pid=5507, parent=None

2019-32-17 23:32:49 5bf0d4db   $ /usr/local/sbin/python examples/script1.py
  pid=5507, parent=0ec9e154

2019-32-17 23:32:49 b3ba09ec     $ /usr/local/bin/python examples/script1.py
  pid=5507, parent=5bf0d4db

2019-32-17 23:32:49 aab37012       $ /usr/sbin/python examples/script1.py
  pid=5507, parent=b3ba09ec

2019-32-17 23:32:49 5bc875fa         $ /usr/bin/python examples/script1.py
  pid=5507, parent=aab37012
  read: /vagrant/examples/script1.py (ecb8231a)
  read: /vagrant/examples/script1.py (ecb8231a)
  read: /vagrant/examples/file1.txt (9736774f)
  write: /vagrant/examples/file2.txt (5e3adc81)

2019-32-17 23:32:49 0e31c866           $
  pid=5508, parent=5bc875fa

2019-32-17 23:32:49 359ae816             $ /bin/sh -c ls
  pid=5508, parent=0e31c866

2019-32-17 23:32:49 23d25168               $
  pid=5509, parent=359ae816

2019-32-17 23:32:49 f79624a6                 $ /bin/ls
  pid=5509, parent=23d25168
```

Each process execution is listed with its start time, process id (pid), and parent pid.
Nested underneath each process header are a series of `read` and `write` lines. These
lines describe each file the process read and wrote to along with a sha1 of the file.
Using the sha1s, tot can determine how the output of one program turns into the
input of another.

To see this, let's execute another program that reads `file2.txt`, removes all the "e"s and writes
the output to `file3.txt`.

```sh
bin/tot log bash -c 'sed s/e// examples/file2.txt > examples/file3.txt'
```

Now let's reimport the logs and show them:

```sh
bin/tot import tot.log tot-fs.log
bin/tot show
```

We should now see a few more lines:

```
2019-07-18 00:07:09 0ba6ccdb $ /bin/bash -c sed s/e// examples/file2.txt > e ...
  pid=6081, parent=None

2019-07-18 00:07:09 120456d7   $
  pid=6082, parent=0ba6ccdb
  write: /vagrant/examples/file3.txt (911648ff)

2019-07-18 00:07:09 d41e183f     $ /bin/sed s/e// examples/file2.txt
  pid=6082, parent=120456d7
  read: /vagrant/examples/file2.txt (5e3adc81)
  write: /vagrant/examples/file3.txt (911648ff)
```

Notice `5e3adc81` is the same hash for the output of our previous command.
If we would like to trace just the interactions with that file sha, we
use it as an argument to `tot show`:

```
bin/tot show  5e3adc81
```

Which should display something like:

```
2019-07-18 00:07:00 a0976032 $ /usr/bin/python examples/script1.py
  proc:  pid=6041
  write: /vagrant/examples/file2.txt (5e3adc81)
2019-07-18 00:07:09 d41e183f $ /bin/sed s/e// examples/file2.txt
  proc:  pid=6082
  read: /vagrant/examples/file2.txt (5e3adc81)
```