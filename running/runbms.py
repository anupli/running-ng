from running.config import load_all
from pathlib import Path


def setup_parser(subparsers):
    f = subparsers.add_parser("runbms")
    f.set_defaults(which="runbms")
    f.add_argument("CONFIG", type=Path)


def run(args):
    if args.get("which") != "runbms":
        return False
    configuration = load_all(args.get("CONFIG"))
    for b in configuration.benchmarks:
        print("{} ".format(b.name), end="")
        for i in range(0, configuration.invocations):
            print(i, end="")
            for j, c in enumerate(configuration.configs):
                jvm = configuration.jvms[c.split('|')[0]]
                mods = [configuration.modifiers[x] for x in c.split('|')[1:]]
                mod_b = b.attach_modifiers(mods)
                if "PASSED" in mod_b.run(jvm):
                    print(chr(ord('a')+j), end="")
                else:
                    print(".", end="")
        print()
    return True
