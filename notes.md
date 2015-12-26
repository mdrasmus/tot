2015-12-26

I need to be able to parse the unfinished and resumed lines.

```
5596  1451148705.750918 execve("/bin/bash", ["bash", "-c", "echo hello | cat > out; cat out"], [/* 15 vars */]) = 0
5596  1451148705.752968 open("/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 4
5596  1451148705.753481 close(4)        = 0
5596  1451148705.753933 open("/lib/x86_64-linux-gnu/libtinfo.so.5", O_RDONLY|O_CLOEXEC) = 4
5596  1451148705.754950 close(4)        = 0
5596  1451148705.755266 open("/lib/x86_64-linux-gnu/libdl.so.2", O_RDONLY|O_CLOEXEC) = 4
5596  1451148705.755934 close(4)        = 0
5596  1451148705.756235 open("/lib/x86_64-linux-gnu/libc.so.6", O_RDONLY|O_CLOEXEC) = 4
5596  1451148705.758306 close(4)        = 0
5596  1451148705.760480 open("/dev/tty", O_RDWR|O_NONBLOCK) = -1 EACCES (Permission denied)
5596  1451148705.761261 open("/usr/lib/locale/locale-archive", O_RDONLY|O_CLOEXEC) = 4
5596  1451148705.762168 close(4)        = 0
5596  1451148705.763791 open("/proc/meminfo", O_RDONLY|O_CLOEXEC) = 4
5596  1451148705.764537 close(4)        = -1 EINVAL (Invalid argument)
5596  1451148705.764935 open("/usr/lib/x86_64-linux-gnu/gconv/gconv-modules.cache", O_RDONLY) = 4
5596  1451148705.766027 close(4)        = 0
5596  1451148705.767700 clone(child_stack=0, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, child_tidptr=0x7fc01b217a10) = 5597
5596  1451148705.767881 close(5)        = 0
5596  1451148705.767921 close(5)        = -1 EBADF (Bad file descriptor)
5596  1451148705.767966 clone(child_stack=0, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, child_tidptr=0x7fc01b217a10) = 5598
5596  1451148705.768076 close(4)        = 0
5598  1451148705.768278 close(4)        = 0
5598  1451148705.769291 open("out", O_WRONLY|O_CREAT|O_TRUNC, 0666 <unfinished ...>
5597  1451148705.769540 close(4)        = 0
5597  1451148705.769584 close(5)        = 0
5597  1451148705.770269 +++ exited with 0 +++
5598  1451148705.772040 <... open resumed> ) = 4
```

This command also needs parsing

```
ls -l /dev/null
```

traces as:
```
lstat("/dev/null", {st_mode=S_IFCHR|0666, st_rdev=makedev(1, 3), ...}) = 0
```

Return value can also be symbolic.
```
lstat("/foo/bar", 0xb004) = -1 ENOENT (No such file or directory)
```

Long strings have ...
```
read(3, "root::0:0:System Administrator:/"..., 1024) = 422
```
But I am not longing reads. Maybe I should so I can link the calls together? No I probably
don't need to log individual reads.


- How to parse unfinished/resumed lines.
  - Each process/thread group (need to learn what threads look like) has only one call
    active at a time. So when I see a `<... $call resumed>` I know it pairs up with the
    last `<unfinished ..>` line of the same process.
  - I could preprocess these lines to repair them, then do normal parsing.

=============================================================================
2015-12-25

- I probably need a root (or separate user) daemon like `tot-server`
  - `tot-server start`
    - start mount at `/var/run/tot/mnt/{session}`
    - or start mount at `/var/run/tot/mnt/{user}`. A sudo-ed setup script
      could make a dir for each user with their own perms.
      - `tot-mount` could then run as the user. This would lead multiple
        mounts, but that's fine. Logs could then be in the user home dir,
        which I perfer anyways.
    - start listening on a socket for IPC?
  - use IPC to start new user sessions?
    - if user knows the session id, that proves they are that user.
  - might need to be root if we ever need to log root actions.
    - `tot` user would not have access to user's files.
- keep `tot-chroot` simple (a separate) since it is sudo-able.
  - How do I know which user to drop perms into? It needs to be provable.
    - User could make a file: `~/.config/tot/passwd` that only the user
      and root have access to.
    - can't put passwd on the command line.
    - can put passwd on stdin.
    - `cat ~/.config/tot/passwd | sudo tot-chroot $user $cmd`
      - Read $user's passwd file to see if it matches what was given on
        command line.
        - make sure passwd in not caught up in logging.
      - run `sudo -u $user strace $strace_args $cmd` to drop perms.
        - for other tracers I could require that they all provide a
          command-line program that provides strace-like behavior.


- The `clone()` call indicates how parent and child process are related.

```
5933  1451078297.634280 clone(child_stack=0, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, child_tidptr=0x7efd651d6a10) = 5934
```

=============================================================================
2015-12-24

- can't fuse libarary `libfuse.so.2`
  - it's because writing to /dev/null is not working. Somehow I am not
    emulating /dev/null correctly.

- normal files have st_mode=33204
- /dev/null is reporting stmode=8630


            5432109876543210
  normal    1000000110110100 33204
  /dev/null 0010000110110110 8630
                   rwxrwxrwx
            ^ ^
            | \------ 2^13 = 8192 = S_IFCHR
            \-------- S_IFREG regular file

- If I let let the mode be a character file S_IFCHR the caller thinks
  it doesn't have permission to open the file. It doesn't even try to open the
  file.
  - Does fuse not work well with character files?
  - For now I can cheat and transform character files into regular.
    - I might have to use directio though in order to be able to lie about
      file st_size.

- binary files are not being read correctly through fuse.

  `diff chroot/mnt/usr/bin/python /usr/bin/python`

  symlinks are being represent correctly. the file size looks like the symlink
  size.
  symlinks are being converted to regular file.

Ok I was able to execute this, use the experimental/fuse/fs.py for mounting.
``
sudo chroot /vagrant/chroot/mnt /vagrant/bin/tot --chroot 123 --log /tmp/a --log-fs /tmp/b ls
```

- ok, I got it working!
  - need to generalize the hard coded paths.
  - my trace logging is also caught up in the fs chroot.
    - could create an escape hatch.
      `/.tot/$path` could allow unrecorded access to `$path`. That way
      `tot` can interact with loggin and config without it being recorded.
    - openning the log file should be in the escape hatch.

  - the tot binary iteself is caught up in the logging, along with all its
    libs.
    - its not terrible, but it adds noise.
    - how do I use the escape hatch for this?
    - maybe I can move the chroot within the strace or just out side the
      strace command.
      - `strace $strace_args $cmd`
      - `chroot /chroot strace $strace_args -o $fifo $cmd`
      - `strace $strace_args -o $fifo tot-chroot $cmd`
        - This would trace any syscalls that tot-chroot does. I could filter
          such logs out myself, if I know how to identify. Basically, by
          pid if I know its pid.
        - There would be fs logs too. Basically reading tot-chroot from disk.
          Perhaps that is regular enough that I can filter out.

  - I still need to drop perms after chroot.

- current design doesn't allow parallel execution of `tot`, because mounting
  would collide.
  - One solution is to just not mount if already mounted.

- Hopefully, by implementing dtrace on mac this will work cross-platform.
  Does anything about my chroot-trick not work on mac?

=============================================================================
2015-12-22

- I tried out my idea of how to capture and *block* all file io.
  - I mount a passthrough fuse filesystem from / to $dir
  - Then I `sudo chroot $dir /bin/bash`
  - From here I can drop perms, chdir, and run the intended command.
- chroot requires root. I don't think even setuid works. So I would need
  to have a daemon that listens through IPC for commands (argv) to run.
  It would maintain the chroot.
  - I wonder if I want one chroot, or if its just easy enough to start a new
    chroot per command.
- Noticed that the passtrhough technique is quite slow. I wonder wether it is:
  - fuse that is slow
  - my use of python that is slow
  - my use of python with logging, and no threads
    - Next thing to do is to try turning this off.
    - I turned it off and its much faster now.
- It is not the chroot that is slow. When I use "bind mounting" it is fast:
  - `sudo mount -o bind / mnt`.


So with this setup, I could now start logging file events:
- File with `filename` on `machine` at time `timestamp` with hash `sha` was
  acted on. Actions include "open for reading" and "closed after writing".
- With just the passthrough fs, I do not know which process did the reading
  or writing. I will need perf events for that.


- ftrace might be closer to what I want. It's a bit confusing where perf_events
  ends and ftrace begins.
  - doc: https://www.kernel.org/doc/Documentation/trace/ftrace.txt

  - all settings are in: /sys/kernel/debug/tracing

  - these files look like could be used to trace just certain processes

    set_ftrace_pid:
	Have the function tracer only trace a single thread.
    set_event_pid:
        Have the events only trace a task with a PID listed in this file.
	Note, sched_switch and sched_wake_up will also trace events
	listed in this file.

  - There is some discussion of callbacks. If I could run my own code
    for each event, I may not need the fuse+chroot trick.

  - kprobe_events: is the "dynamic" tracer. I think what makes this dynamic
    is that can specify your own breakpoints (within a kernel function and
    decide how you want to capture arguments).

  - `instances` directory can be used to create a separate tracing session.
    `mkdir foo` within the instances directory will create a dir `foo` that
    is auto populated with the tracing interface.

- uprobe_events:
  - Is userspace tracing relavent? Could I capture syscalls from the userland
    side?

- systemtap:
  - https://sourceware.org/systemtap/examples/process/strace.stp
  - https://sourceware.org/systemtap/examples/process/strace.txt
  - can reimplement strace using systemtap script.
  - is it faster than strace?
    - http://elinux.org/System_Tap
    - maybe 5%
    - https://sysdig.com/sysdig-vs-dtrace-vs-strace-a-technical-discussion/
  - is it easy to use without recompiling the kernel?
    - it is being a pain to install, because you need to fetch kernel symbols.
  - looks like I can use the strace.stp script without kernel debug symbols.

- dtrace
  https://github.com/dtrace4linux/linux

=============================================================================
2015-12-21

- Current idea for the architecture:
  - Recording:
    - prefix command like `totes myprog arg1 arg2`
    - sends/stores logs to common location.
  - Database
    - Add logs to a db: `totes db add log-file.json`
    - Adding should dedup log lines.
    - Logs from different machines can all be combined. If any sha's are shared
      we can connect the graph together.
  - Command line inspector
    - `totes show file` could show all commands that made the file in
      reverse chronological order.
  - Web client for db
    - Visualize process-file graph.

- Recording on mac:
  - dtrace/dtruss can be used.
- Recording on Linux:
  - perf_events

- perf_events:
  - Example of recording file opens:
    - http://www.brendangregg.com/blog/2014-07-25/opensnoop-for-linux.html
    - https://github.com/brendangregg/perf-tools/blob/master/opensnoop
  - Use at netflix:
    - http://www.slideshare.net/brendangregg/scale2015-linux-perfprofiling

```sh
perf probe --add 'do_sys_open filename:string'
perf record --no-buffering -e probe:do_sys_open -o - -a | PAGER=cat perf script -i -
perf probe --del do_sys_open
```

This does work.
```sh
sudo echo 0 > /proc/sys/kernel/kptr_restrict
sudo perf record -e fs:do_sys_open -a
sudo perf script
```

Is it possible to do something just in userland though? What is uprobe?


```
sudo perf probe 'do_sys_open filename:string'
```

It seems I don't have everything enabled:
```
Failed to find path of kernel module.
Failed to open debuginfo file.
  Error: Failed to add events. (-2)
```
