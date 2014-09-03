from cStringIO import StringIO


def proc_exec(proc, verbose):
    # execute the process ... .wait()
    if verbose:
        proc_output = StringIO()
        while proc.poll() is None:
            line = proc.stdout.readline()
            print line,
            proc_output.write(line)
        msg = ''.join(proc_output)
    else:
        msg = ''.join(proc.communicate())
    return msg
