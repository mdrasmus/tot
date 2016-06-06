from difflib import unified_diff
from StringIO import StringIO
from unittest import TestCase

from tot.config import Session
from tot.tracer.strace import STraceTracer
from tot.logger import Logger


# Set this to True to record new test data.
record_test = False


class TestSTrace(TestCase):

    session_id = 'session_id'

    def setUp(self):
        self.session = Session(id=self.session_id)

    def assertEqualFile(self, value, filename):
        if record_test:
            with open(filename, 'w') as out:
                out.write(value)
        else:
            with open(filename) as infile:
                value2 = infile.read()

            if value != value2:
                diff = '\n'.join(unified_diff(
                    value2.split('\n'),
                    value.split('\n')
                ))
                print diff
                self.fail()

    def test_parse_logs(self):
        out_stream = StringIO()
        logger = Logger(out_stream)
        tracer = STraceTracer(self.session)

        with open('tot/test_data/strace_ls.log') as stream:
            for row in tracer._parse_strace(stream):
                logger.log(row)

        self.assertEqualFile(
            out_stream.getvalue(), 'tot/test_data/strace_ls.json')

    def test_preprocess(self):
        infile = open('tot/test_data/strace_unfinished.log')
        tracer = STraceTracer(self.session)
        result = ''.join(line for line in tracer._preprocess(infile))

        self.assertEqualFile(
            result, 'tot/test_data/strace_unfinished.expected')
