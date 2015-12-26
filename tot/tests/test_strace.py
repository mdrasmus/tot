from StringIO import StringIO
from unittest import TestCase

from tot.tracer.strace import STraceTracer
from tot.logger import Logger


# Set this to True to record new test data.
record_test = False


class TestSTrace(TestCase):

    def assertEqualFile(self, value, filename):
        if record_test:
            with open(filename, 'w') as out:
                out.write(value)
        else:
            with open(filename) as infile:
                self.assertEqual(infile.read(), value)

    def test_parse_logs(self):
        out_stream = StringIO()
        logger = Logger(out_stream)
        tracer = STraceTracer()

        with open('tot/test_data/strace_ls.log') as stream:
            for row in tracer._parse_strace(stream):
                logger.log(row)

        self.assertEqualFile(
            out_stream.getvalue(), 'tot/test_data/strace_ls.json')

    def test_preprocess(self):
        infile = open('tot/test_data/strace_unfinished.log')
        tracer = STraceTracer()
        result = ''.join(line for line in tracer._preprocess(infile))

        self.assertEqualFile(
            result, 'tot/test_data/strace_unfinished.expected')
