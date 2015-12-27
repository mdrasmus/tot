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
            (10542, u'dc13111781e4e337b16dd3c75e143055d74f8566'),
            (10543, u'ad405e0398d0dee7a22f346a48b82fa8bd6f272f'),
            (10544, u'4e6607fd3ee39bae479871e9297cbf36c2ac69c3'),
            (10544, u'2896330bf2b3ccb5aee09f8e66dcd01f4a3a3d27'),
        ]

        self.assertEqual(proc_ids, expected_proc_ids)
