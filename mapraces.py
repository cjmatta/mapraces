#!/bin/env python
# mapraces
# A small script to improve the user experience using MapR ACEs
import sys
import os
import re
import logging
from optparse import OptionParser, OptionGroup, OptParseError
import subprocess
from subprocess import CalledProcessError
import itertools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('mapraces')

PERMS = ['readfile', 'writefile', 'executefile',
'readdir', 'addchild', 'deletechild', 'lookupdir']

HADOOP_BIN = ''
if os.getenv("HADOOP_HOME") is not None:
    HADOOP_BIN = os.path.join(os.getenv("HADOOP_HOME"), 'bin', 'hadoop')

if not os.path.exists(HADOOP_BIN):
    logger.error("hadoop binary not found, please export $HADOOP_HOME it and retry.")
    sys.exit(1)

# need a global here to handle the repeated callback for the aces.
NEW_ACES = {}

def get_aces(f):
    aces = {}
    try:
        current_aces = subprocess.check_output([HADOOP_BIN, 'mfs', '-getace', f])
        print current_aces.split()
        for (index, value) in enumerate(current_aces.split()):
            if re.search('^.*\:', value):
                (k, v) = value.split(':')
                if k in PERMS:
                    aces[k] = v
        return aces
    except CalledProcessError, e:
        print e
        sys.exit(1)

# Build and run command
def set_aces(f, aces, recursive, inherit, preservemodebits):
    aces_list = [("-%s" % perm, aces[perm]) for perm in aces]
    aces_list = list(itertools.chain.from_iterable(aces_list))
    try:
        command = [HADOOP_BIN, 'mfs', '-setace']
        if recursive:
            command.append('-R')

        [command.append(x) for x in aces_list]

        if inherit:
            command.append('-setinherit')
            command.append('true')

        if preservemodebits:
            command.append('-preservemodebits')
            command.append('true')

        command.append(f)
        logger.info("Running command: %s" % ' '.join(command))
        subprocess.check_call(command)
    except CalledProcessError as e:
        logger.warn(e.output)
        sys.exit(e.returncode)

def capture_ace(option, opt_str, value, parser):
    NEW_ACES[option.dest] = value

# Resolves the current and new ACE into a final ACE
def add_ace(current, new):
    final_aces = {}
    for perm in new:
        if current[perm] != '':
            new_expressions = new[perm].split(',')
            current_expressions = current[perm].split(',')
            # resolve duplicates and return list.
            final_aces[perm] = ','.join(
                            list(
                                set(current_expressions).union(new_expressions)
                                )
                            )
    print current
    print new
    return final_aces

def remove_ace(ace, current):
    pass

class MyOptionParser(OptionParser):
    def error(self, msg):
        self.print_help(sys.stderr)
        self.exit(2, "%s: error: %s\n" % (self.get_prog_name(), msg))

def main():
    parser = MyOptionParser()
    parser.add_option("-a", "--add", action="store_true", dest="addace",
        help="Add ACE")
    parser.add_option("-d", "--delete", action="store_true", dest="delace",
        help="Delete ACE")
    parser.add_option("-R", action="store_true", dest="recursive",
        help="Recursively set ACE")
    parser.add_option("--setinherit", dest="setinherit", metavar="[true|false]",
        help="Weather or not to aces will inherit to children")
    parser.add_option("--preservemodebits", dest="preservemodebits", metavar="[true|false]",
        help="Weather or not to preserve mode bits")
    perm_group = OptionGroup(parser, "ACE Permissions",
        "Set one (or more) of the following ACE permissions")
    perm_group.add_option("--readfile", action="callback", callback=capture_ace, type=str, dest="readfile", help="reafile ACE")
    perm_group.add_option("--writefile", action="callback", callback=capture_ace, type=str, dest="writefile", help="writefile ACE")
    perm_group.add_option("--executefile", action="callback", callback=capture_ace, type=str, dest="executefile", help="executefile ACE")
    perm_group.add_option("--readdir", action="callback", callback=capture_ace, type=str, dest="readdir", help="readdir ACE")
    perm_group.add_option("--addchild", action="callback", callback=capture_ace, type=str, dest="addchild", help="addchild ACE")
    perm_group.add_option("--deletechild", action="callback", callback=capture_ace, type=str, dest="deletechild", help="deletechild ACE")
    perm_group.add_option("--lookupdir", action="callback", callback=capture_ace, type=str, dest="lookupdir", help="lookupdir ACE")
    parser.add_option_group(perm_group)

    (options, args) = parser.parse_args()
    # require either add or delete
    if not options.addace and not options.delace:
        parser.error("--add or --delete required.")
    # Check for add/del exclusivity
    if options.addace and options.delace:
        parser.error("Options for add ace and delete ace are mutually exclusive")
    # convert true/false on command line to True False
    if options.setinherit:
        if options.setinherit.strip() not in ["true", "True", "false", "False"]:
            parser.error("Please specify only true or false for --setinherit")
        elif options.setinherit.strip() in ["true", "True"]:
            options.setinherit = True
        elif options.setinherit.strip() in ["false", "False"]:
            options.setinherit = False
    if options.preservemodebits:
        if options.preservemodebits.strip() not in ["true", "True", "false", "False"]:
            parser.error("Please specify only true or false for --preservemodebits")
        elif options.preservemodebits.strip() in ["true", "True"]:
            options.preservemodebits = True
        elif options.preservemodebits.strip() in ["false", "False"]:
            options.preservemodebits = False

    # Check for missing filename
    if len(args) == 0:
        parser.error("Filename required!")

    if len(args) > 1:
        parser.error("Please specify only one file or directory at a time.")


    current_aces = get_aces(args[0])

    if options.addace:
        add_ace(current_aces, NEW_ACES)

    set_aces(args[0], NEW_ACES, options.recursive, options.setinherit, options.preservemodebits)

if __name__ == '__main__':
    main()
