# -*- coding: utf-8 -*-
import logging
LOG = logging.getLogger(__file__)

from cStringIO import StringIO
import os


def proc_exec(proc, verbose):
    # execute the process ... .wait()
    proc_output = StringIO()

    while proc.poll() is None:
        line = proc.stdout.read()
        if verbose:
            print line
        proc_output.write(line)
    msg = ''.join(proc_output.getvalue())

    return msg


def is_file_readable(path):
    if os.path.isfile(path):
        if os.access(path, os.R_OK):
            return True
        else:
            LOG.error('Missing read permission: %s', path)
    else:
        LOG.error('File not found: %s', path)
        return False
