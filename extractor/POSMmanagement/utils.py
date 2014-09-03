from cStringIO import StringIO


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
