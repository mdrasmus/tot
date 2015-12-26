from StringIO import StringIO
from unittest import TestCase

from tot.tracer.strace import STraceTracer
from tot.logger import Logger


# Set this to True to record new test data.
record_test = False


class TestSTrace(TestCase):

    def test_parse_logs(self):
        out_stream = StringIO()
        logger = Logger(out_stream)
        tracer = STraceTracer()

        with open('tot/test_data/strace_ls.log') as stream:
            for row in tracer._parse_strace(stream):
                logger.log(row)

        if record_test:
            with open('tot/test_data/strace_ls.json', 'w') as out:
                out.write(out_stream.getvalue())
        else:
            with open('tot/test_data/strace_ls.json') as infile:
                self.assertEqual(infile.read(), out_stream.getvalue())
