# -*- coding: utf-8 -*-
import logging
LOG = logging.getLogger(__file__)

from io import StringIO

import os
import time
import subprocess
import threading
from queue import Queue


# http://stefaanlippens.net/python-asynchronous-subprocess-pipe-reading
class AsynchronousFileReader(threading.Thread):
    '''
    Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    '''

    def __init__(self, fd, queue):
        assert isinstance(queue, Queue)
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


def gather_output(proc):
    for stdout_line in iter(proc.stdout.readline, ""):
        yield stdout_line
    proc.stdout.close()
    proc.wait()

def proc_exec(cmd, verbose=None):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    output = ""
    for line in gather_output(proc):
        print(line, end="")
        output += line

    return proc.returncode, output

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
