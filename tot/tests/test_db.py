from unittest import TestCase

from tot.db import FileEvent
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

        # Ensure all processes and their task ids were loaded correctly.
        procs = self.db.session.query(Process).order_by('start_time').all()
        proc_ids = [(proc.pid, proc.id) for proc in procs]
        expected_proc_ids = [
            (10542, 'dc13111781e4e337b16dd3c75e143055d74f8566'),
            (10543, '311e28603fb90fd5e45b13cc7e2de8315fa442e3'),
            (10544, 'e48f7cb7d841433df800ef77d9185214715d6e0a'),
            (10544, '2896330bf2b3ccb5aee09f8e66dcd01f4a3a3d27'),
        ]
        self.assertEqual(proc_ids, expected_proc_ids)

        # Ensure that filename info was copied through fds correctly.
        file_events = (self.db.session.query(FileEvent)
                       .filter_by(action='write'))
        self.assertEqual(
            sorted((f.filename, f.action) for f in file_events),
            [('/vagrant/tmp/out', 'write'),
             ('/vagrant/tmp/out', 'write')],
        )
