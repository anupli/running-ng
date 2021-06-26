from running.config import Configuration
from pathlib import Path


def setup_parser(subparsers):
    f = subparsers.add_parser("runbms")
    f.set_defaults(which="runbms")
    f.add_argument("CONFIG", type=Path)


def run(args):
    if args.get("which") != "runbms":
        return False
    configuration = Configuration.from_file(args.get("CONFIG"))
    configuration.resolve_class()
    for suite_name, bms in configuration.get("benchmarks").items():
        for b in bms:
            print(b.name, end=" ")
            for i in range(0, configuration.get("invocations")):
                print(i, end="", flush=True)
                for j, c in enumerate(configuration.get("configs")):
                    jvm = configuration.get("jvms")[c.split('|')[0]]
                    mods = [configuration.get("modifiers")[x]
                            for x in c.split('|')[1:]]
                    mod_b = b.attach_modifiers(mods)
                    if "PASSED" in mod_b.run(jvm):
                        print(chr(ord('a')+j), end="", flush=True)
                    else:
                        print(".", end="", flush=True)
            print()
    return True
