import os
import re
from subprocess import call
import tempfile
import thread

import tot.tracer


def parse_arg(arg):
    try:
        return int(arg)
    except ValueError:
        pass

    try:
        return float(arg)
    except ValueError:
        pass

    return arg


class STraceTracer(tot.tracer.Tracer):

    def trace(self, cmd):
        self._make_fifo()

        thread.start_new_thread(self._run_trace, (cmd,))

        with open(self._fifo) as stream:
            for row in self._parse_strace(stream):
                yield row

        self._cleanup_fifo()

    def _make_fifo(self):
        self._tmp_path = tempfile.mkdtemp(prefix='tot_')
        self._fifo = os.path.join(self._tmp_path, 'fifo')
        os.mkfifo(self._fifo)

    def _cleanup_fifo(self):
        os.unlink(self._fifo)
        os.rmdir(self._tmp_path)

        self._fifo = None
        self._tmp_path = None

    def _run_trace(self, cmd):
        self.retcode = call([
            'strace', '-ttt', '-f',
            '-e', 'trace=execve,clone,fork,vfork,open,close,dup,dup2,pipe',
            '-o', self._fifo] + cmd)

    def _parse_args(self, expr):

        def parse_string(i):
            assert expr[i] == '"'
            value = []

            i += 1
            while expr[i] != '"':
                if expr[i] == '\\':
                    # Skip next char.
                    i += 1
                    continue
                else:
                    value.append(expr[i])
                    i += 1

            return i + 1, ''.join(value)

        def parse_simple_value(i):
            value = []
            while i < len(expr):
                c = expr[i]
                if c in '),] ':
                    # End of value.
                    break
                else:
                    value.append(c)
                    i += 1

            return i, ''.join(value)

        def parse_list(i):
            args = []
            arg = []
            within_arg = False
            is_string = True

            while i < len(expr):
                c = expr[i]

                # Consume whitespace.
                if c in ', ':
                    i += 1

                elif c == '"':
                    # Start of string.
                    i, string = parse_string(i)
                    args.append(string)

                elif c == '[':
                    # Start of new list
                    i, args2 = parse_list(i + 1)
                    args.append(args2)

                elif c in '])':
                    # End of list.
                    i += 1
                    break

                elif c == '/':
                    # Start of comment.
                    i = expr.find('/', i + 1) + 1

                else:
                    # Simple value.
                    i, value = parse_simple_value(i)
                    args.append(parse_arg(value))

            return i, args

        i = 0
        i, args = parse_list(i)

        return args

    def _parse_strace_line(self, line):
        """
        Parse an strace line.
        """
        pid, timestamp, rest = line.split(None, 2)
        pid = int(pid)

        # TODO: also parse `+++ killed by SIGINT +++`
        exit_groups = re.match('\+\+\+ exited with (\d+) \+\+\+', rest)
        signal_groups = re.match('--- SIGCHLD .* ---', rest)

        if exit_groups:
            # Process exit event.
            func = 'exit'
            args = []
            result = int(exit_groups.groups()[0])
        elif signal_groups:
            # Not logging signals currently.
            return None
        else:
            # Syscall event.
            func, rest = rest.split('(', 1)
            args = self._parse_args(rest)

            # Parse return value.
            i = rest.rfind('=')
            if i != -1:
                result = parse_arg(rest[i + 1:].strip())
            else:
                result = None

        return {
            'type': 'trace',
            'session': self.session.id,
            'host': self.session.host,
            'user': self.session.user,
            'pid': pid,
            'timestamp': timestamp,
            'func': func,
            'args': args,
            'return': result,
        }

    def _preprocess(self, stream):
        """
        Preprocess strace stream to remove all concurrent logging lines.
        """
        unfinished = ' <unfinished ...>'
        resumed = '<... [^ ]+ resumed> (.*)$'
        in_progressed = {}

        for line in stream:
            pid, timestamp, rest = line.rstrip().split(None, 2)

            # Save any lines that are unfinished.
            # Line must *end* with the string unfinished.
            i = rest.rfind(unfinished)
            if i != -1 and i == len(rest) - len(unfinished):
                partial_line = rest[:i]
                in_progressed[pid] = (timestamp, partial_line)
                continue

            # Resume lines. Line must *start* with resumed string.
            match = re.search(resumed, line)
            if match:
                resumed_line = match.groups()[0]
                timestamp, partial_line = in_progressed.pop(pid)
                line = '{}  {} {}{}'.format(
                    pid, timestamp, partial_line, resumed_line)

            yield line

    def _parse_strace(self, stream):
        stream = self._preprocess(stream)
        for line in stream:
            row = self._parse_strace_line(line)
            if row:
                yield row
