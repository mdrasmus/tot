from collections import defaultdict
import datetime
import hashlib
import json
import os
import time
import uuid

import sqlalchemy as sqla
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker


Model = declarative_base()


class Session(Model):
    __tablename__ = 'session'

    id = Column(String, primary_key=True)  # UUID
    user = Column(String)
    host = Column(String)


class Process(Model):
    __tablename__ = 'process'

    id = Column(String, primary_key=True)  # UUID
    pid = Column(Integer)
    parent = Column(String, sqla.ForeignKey('process.id'), nullable=True)
    progname = Column(String)
    argv = Column(String)  # json
    exit_value = Column(Integer, nullable=True)
    session = Column(String, sqla.ForeignKey('session.id'), nullable=True)
    start_time = Column(DateTime)
    stop_time = Column(DateTime, nullable=True)


class FileEvent(Model):
    __tablename__ = 'file_event'

    id = Column(Integer, primary_key=True)
    process = Column(String, sqla.ForeignKey('process.id'))
    action = Column(String)
    filename = Column(String)
    timestamp = Column(DateTime)


class FileState(Model):
    __tablename__ = 'file_state'

    id = Column(Integer, primary_key=True)
    session = Column(String, sqla.ForeignKey('session.id'), nullable=True)
    filename = Column(String)
    hash = Column(String)
    timestamp = Column(DateTime)


class ProcessFile(Model):
    __tablename__ = 'process_file'

    id = Column(Integer, primary_key=True)
    process = Column(String, sqla.ForeignKey('process.id'))
    action = Column(String)
    filename = Column(String)
    hash = Column(String)


class TotDatabase(object):
    """
    Database of tot logs.
    """

    def __init__(self, db_file=None, echo=False, reset=False):
        if db_file:
            self.connect(db_file, echo=echo, reset=reset)

    def connect(self, db_file, echo=False, reset=False):
        self.db_file = db_file

        if reset:
            if os.path.exists(self.db_file):
                os.remove(self.db_file)

        # Create database.
        self.uri = 'sqlite:///' + self.db_file
        self.engine = sqla.create_engine(self.uri, echo=echo)

        # Create schema.
        Model.metadata.create_all(self.engine)

        # Get new ORM session.
        self.Session = sessionmaker()
        self.Session.configure(bind=self.engine)
        self.session = self.Session()

    def new_task_id(self, session_id, pid, timestamp):
        """
        Create a deterministic globally unique task id using hashing.
        """
        m = hashlib.sha1()
        text = '{}:{}:{}'.format(session_id, pid, timestamp)
        m.update(text)
        return m.digest().encode("hex")

    def parse_timestamp(self, timestamp_str):
        timestamp = datetime.datetime.fromtimestamp(float(timestamp_str))
        return timestamp

    def parse_open_mode(self, mode_str):
        name2bit = {
            'O_RDONLY': os.O_RDONLY,
            'O_WRONLY': os.O_WRONLY,
            'O_RDWR': os.O_RDWR,
            'O_NONBLOCK': os.O_NONBLOCK,
            'O_APPEND': os.O_APPEND,
            'O_CREAT': os.O_CREAT,
            'O_TRUNC': os.O_TRUNC,
            'O_EXCL': os.O_EXCL,
            'O_NOFOLLOW': os.O_NOFOLLOW,
        }
        value = 0
        for name in mode_str.split('|'):
            value |= name2bit.get(name, 0)
        return value

    def parse_fd(self, value):
        if isinstance(value, basestring):
            return int(value.split(' ', 1)[0])
        else:
            return value

    def load(self, logs):
        """
        Load tot logs into database.
        """

        class ProcInfo(object):
            def __init__(self, pid, task_id, cwd='', parent=None):
                self.pid = pid
                self.task_id = task_id
                self.fds = {}
                self.cwd = cwd

                if parent:
                    self.fds = dict(parent.fds)
                    self.cwd = parent.cwd

        sessions_cwd = ''
        procs = {}

        for row in logs:
            if row['type'] == 'trace':
                if row['func'] == 'init':
                    [session_cwd] = row['args']

                elif row['func'] == 'execve':
                    # New task.
                    proc = procs.get(row['pid'])
                    child_task_id = self.new_task_id(
                        row['session'], row['pid'], row['timestamp'])
                    if not proc:
                        # First process of the session.
                        procs[row['pid']] = ProcInfo(
                            row['pid'], child_task_id, session_cwd)
                        parent_task_id = None
                    else:
                        # Update task id.
                        parent_task_id = proc.task_id
                        proc.task_id = child_task_id

                    self.load_start_process(
                        session_id=row['session'],
                        id=child_task_id,
                        pid=row['pid'],
                        parent_id=parent_task_id,
                        progname=row['args'][0],
                        argv=row['args'][1],
                        start_time=self.parse_timestamp(row['timestamp']),
                    )

                elif row['func'] in ('clone', 'fork', 'forkv'):
                    child_id = row['return']
                    parent_proc = procs[row['pid']]
                    child_task_id = self.new_task_id(
                        row['session'], child_id, row['timestamp'])
                    procs[child_id] = ProcInfo(
                        child_id, child_task_id, parent=parent_proc)

                    self.load_start_process(
                        session_id=row['session'],
                        id=child_task_id,
                        pid=child_id,
                        parent_id=parent_proc.task_id,
                        progname=None,
                        argv=None,
                        start_time=self.parse_timestamp(row['timestamp']),
                    )

                elif row['func'] == 'exit':
                    self.load_stop_process(
                        id=procs[row['pid']].task_id,
                        exit_value=row['return'],
                        stop_time=self.parse_timestamp(row['timestamp']),
                    )

                elif row['func'] == 'open':
                    args = row['args']
                    if len(args) == 2:
                        filename, mode = args
                        flags = 0
                    else:
                        filename, mode, flags = args

                    mode = self.parse_open_mode(mode)
                    fd = self.parse_fd(row['return'])

                    proc = procs[row['pid']]

                    # Convert relative filenames to absolute.
                    if not filename.startswith('/'):
                        filename = os.path.join(proc.cwd, filename)

                    proc.fds[fd] = (filename, mode)

                    if mode == os.O_RDONLY:
                        self.load_file_event(
                            proc.task_id,
                            'read',
                            filename,
                            self.parse_timestamp(row['timestamp']),
                        )

                elif row['func'] in ('dup', 'dup2'):
                    old_fd = row['args'][0]
                    new_fd = row['return']

                    if new_fd != -1:
                        proc = procs[row['pid']]
                        file_info = proc.fds.get(old_fd)
                        if file_info:
                            proc.fds[new_fd] = file_info

                elif row['func'] == 'close':
                    fd = row['args'][0]
                    proc = procs[row['pid']]
                    file_info = proc.fds.get(fd)
                    if not file_info:
                        continue

                    filename, mode = file_info

                    if mode & os.O_WRONLY:
                        self.load_file_event(
                            proc.task_id,
                            'write',
                            filename,
                            self.parse_timestamp(row['timestamp']),
                        )

            elif row['type'] == 'fs':
                if row.get('hash'):
                    self.load_file_state(
                        session_id=row['session'],
                        filename=row['path'],
                        hash=row['hash'],
                        timestamp=self.parse_timestamp(row['timestamp']),
                    )

        self.session.commit()

        self.load_process_files()

    def load_process_files(self):

        print self.session.query(FileEvent).count()
        print self.session.query(FileState).count()

    def load_start_process(self, session_id, id, pid, parent_id,
                           progname, argv, start_time):
        if argv is None:
            argv_str = ''
        else:
            argv_str = json.dumps(argv, sort_keys=True, separators=(',', ':'))

        self.session.add(Process(
            id=id,
            pid=pid,
            parent=parent_id,
            progname=progname or '',
            argv=argv_str,
            exit_value=None,
            session=None,
            start_time=start_time,
            stop_time=None,
        ))

    def load_stop_process(self, id, exit_value, stop_time):
        self.session.query(Process).filter_by(id=id).update({
            'exit_value': exit_value,
            'stop_time': stop_time,
        })

        # TODO: if argv=None, then I know my stop time should be the same as
        # my parent (ancestor).

    def load_file_event(self, process_id, action, filename, timestamp):
        self.session.add(FileEvent(
            process=process_id,
            action=action,
            filename=filename,
            timestamp=timestamp,
        ))

    def load_file_state(self, session_id, filename, hash, timestamp):

        self.session.add(FileState(
            session=None,
            filename=filename,
            hash=hash,
            timestamp=timestamp,
        ))
