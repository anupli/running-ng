from typing import Optional, Iterable, Callable
import subprocess


def fillin(callback: Callable[[int, Iterable[int]], None], levels: int, start: Optional[int] = None):
    """Fill the parameter space

    The parameter space is from 0, 1, 2, ..., 2^levels (not right-inclusive).

    The advantage of using this function is that it fills in the points in the
    space logarithmically, starting with the ends and middle, and progressing
    until all 2^levels + 1 points are explored.

    Parameters
    ----------
    callback : Callable[[int, Iterable[int]], None]
        The arguments represent a list of fractions.
        For example, callback(8, [2, 6]) means 2/8 and 6/8.
    levels : int
        The log value of the size of the parameter space.
    start: Optional[int]
        Instead of starting from 0, start from a specified value.
    """
    commenced = False
    if start is None:
        callback(2**levels, range(0, 2 ** levels + 1, 2**(levels-1)))
        commenced = True
    i = 1
    while i < levels:
        base = 2 ** (levels - 1 - i)  # larger i, smaller base
        step = 2 ** (levels - i)  # larger i, smaller step
        if start is not None and base == start:
            commenced = True
        if commenced:
            callback(2**levels, range(base, 2 ** levels, step))
        i += 1


def cmd_program(prog) -> Callable[[int, Iterable[int]], None]:
    def callback(end, ns):
        cmd = [prog]
        cmd.append(str(end))
        cmd.extend(map(str, ns))
        output = subprocess.check_output(cmd)
        print(output.decode("utf-8"), end="")
    return callback


def setup_parser(subparsers):
    f = subparsers.add_parser("fillin")
    f.set_defaults(which="fillin")
    f.add_argument("PROG")
    f.add_argument("LEVELS", type=int)
    f.add_argument("START", type=int, nargs='?', default=None)


def run(args):
    if args.get("which") != "fillin":
        return False
    callback = cmd_program(args.get("PROG"))
    fillin(callback, args.get("LEVELS"), args.get("START"))
    return True
