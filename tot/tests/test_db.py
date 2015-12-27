from unittest import TestCase

from tot.db import Process
from tot.db import TotDatabase
from tot.logger import read_logs


# Set this to True to record new test data.
record_test = False


class TestDB(TestCase):

    def setUp(self):
        self.db = TotDatabase(':memory:')

    def assertEqualFile(self, value, filename):
        if record_test:
            with open(filename, 'w') as out:
                out.write(value)
        else:
            with open(filename) as infile:
                self.assertEqual(infile.read(), value)

    def test_load(self):
        rows = read_logs('tot/test_data/chdir.log')
        self.db.load(rows)

        procs = self.db.session.query(Process).order_by('start_time').all()
        proc_ids = [(proc.pid, proc.id) for proc in procs]

        expected_proc_ids = [
            (10542, '104bfa6c4a029883d2fd9961b3adbabc02f4ac11'),
            (10543, '5786b61d85f9d24f3b14347ecd0a507bdbf19933'),
            (10544, '68086d14901c8e2094d9998a9e40eddc094f1836'),
            (10544, '72e5c05bd457db4a8affd2d0425d3be42d92f026'),
        ]

        self.assertEqual(proc_ids, expected_proc_ids)
