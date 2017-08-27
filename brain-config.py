#!/usr/bin/env python3
import argparse, brain, sys


def read_item(brain, item):
    print('{}: {}'.format(item, brain[item]))

def write_item(brain, str):
    if str.count('=') != 1:
        raise ValueError('Invalid name=val write string')

    item, val = str.split('=')
    val = int(val, 0)

    old = brain[item]
    brain[item] = val
    print('{}: {} -> {}'.format(item, old, brain[item]))

def read_all(b):
    for it in brain.GLOBAL_FIELDS:
        read_item(b, 'global.'+it)
    for i in range(3):
        for it in brain.SETUP_FIELDS:
            read_item(b, 'setup{}.{}'.format(i+1, it))

    # We've done enough.
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description='Modify Brain FBL unit configuration',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog='''

Read and write configuration parameters to a Brain FBL unit. A configuration
parameter is a two-level entity, with a namespace of either "global", "setup1",
"setup2", or "setup3". Global and setup have differing permitted fields (listed
in fields.py).

When writing, the value is a 16-bit integer which may be given in either decimal
or hexadecimal form.

Example usage:

$ ./brain-config.py /dev/ttyUSB0 --read global.GovDiv
global.GovDiv: 2100

$ ./brain-config.py /dev/ttyUSB0 --write global.GovDiv=42
global.GovDiv: 2100 -> 42

$ ./brain-config.py /dev/ttyUSB0 --write global.GovDiv=0x834
global.GovDiv: 42 -> 2100

$ ./brain-config.py /dev/ttyUSB0 --read setup1.TailGainA
setup1.TailGainA: 32767
''')
    parser.add_argument('device')
    parser.add_argument('--read', action='append', help='Read a configuration parameter. E.g. global.RxType')
    parser.add_argument('--read-all', action='store_true', help='Read all known configuration parameters')
    parser.add_argument('--write', action='append', help='Write a configuation parameter. Expects name=val pairs')
    try:
        args = parser.parse_args()
    except:
        print('Error: invalid arguments on command line')
        parser.print_help()
        sys.exit(1)

    b = brain.Brain(args.device)

    if args.read_all:
        read_all(b)

    if args.read:
        for parm in args.read:
            read_item(b, parm)

    if args.write:
        for parm in args.write:
            write_item(b, parm)

if __name__ == '__main__':
    main()
