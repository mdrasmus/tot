import json


class Logger(object):

    def __init__(self, stream):
        self.stream = stream

    def log(self, row):
        self.stream.write(
            json.dumps(row, sort_keys=True, separators=(',', ':')))
        self.stream.write('\n')
        self.stream.flush()


def read_logs(stream_or_filename):
    """
    Iterate through a tot log file.
    """
    if isinstance(stream_or_filename, basestring):
        stream = open(stream_or_filename)
        close_needed = True
    else:
        stream = stream_or_filename
        close_needed = False

    try:
        for line in stream:
            yield json.loads(line)
    finally:
        if close_needed:
            stream.close()
