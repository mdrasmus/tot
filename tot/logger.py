import json


class Logger(object):

    def __init__(self, stream):
        self.stream = stream

    def log(self, row):
        self.stream.write(json.dumps(row, sort_keys=True))
        self.stream.write('\n')
        self.stream.flush()
