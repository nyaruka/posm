# -*- coding: utf-8 -*-
import logging
LOG = logging.getLogger(__file__)

from cStringIO import StringIO

import os
import time
import threading
import Queue


# http://stefaanlippens.net/python-asynchronous-subprocess-pipe-reading
class AsynchronousFileReader(threading.Thread):
    '''
    Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    '''

    def __init__(self, fd, queue):
        assert isinstance(queue, Queue.Queue)
        assert callable(fd.readline)
        threading.Thread.__init__(self)
        self._fd = fd
        self._queue = queue

    def run(self):
        '''The body of the tread: read lines and put them on the queue.'''
        for line in iter(self._fd.readline, ''):
            self._queue.put(line)

    def eof(self):
        '''Check whether there is no more content to expect.'''
        return not self.is_alive() and self._queue.empty()


def proc_exec(proc, verbose):
    # execute the process ... .wait()
    proc_output = StringIO()

    # Launch the asynchronous readers of the process' stdout and stderr.
    stdout_queue = Queue.Queue()
    stdout_reader = AsynchronousFileReader(proc.stdout, stdout_queue)
    stdout_reader.start()
    stderr_queue = Queue.Queue()
    stderr_reader = AsynchronousFileReader(proc.stderr, stderr_queue)
    stderr_reader.start()

    # Check the queues if we received some output (until there is nothing more
    # to get).
    while proc.poll() is None:
        while not stdout_reader.eof() or not stderr_reader.eof():
            # Show what we received from standard output.
            while not stdout_queue.empty():
                line = stdout_queue.get()
                if verbose:
                    print line,
                proc_output.write(line)

            # Show what we received from standard error.
            while not stderr_queue.empty():
                line = stderr_queue.get()
                if verbose:
                    print line,
                proc_output.write(line)

            # Sleep a bit before asking the readers again.
            time.sleep(.1)

    # Let's be tidy and join the threads we've started.
    stdout_reader.join()
    stderr_reader.join()

    # Close subprocess' file descriptors.
    proc.stdout.close()
    proc.stderr.close()

    msg = ''.join(proc_output.getvalue())

    return msg


def is_directory_writable(path):
    if os.path.isdir(path):
        if os.access(path, os.W_OK):
            return True
        else:
            LOG.error('Missing write permission: %s', path)
    else:
        LOG.error('Directory not found: %s', path)

    return False


def is_file_readable(path):
    if os.path.isfile(path):
        if os.access(path, os.R_OK):
            return True
        else:
            LOG.error('Missing read permission: %s', path)
    else:
        LOG.error('File not found: %s', path)

    return False
