#!/usr/bin/env python3

import logging
import os
import re
import shlex
import shutil
import subprocess
import sys

def main():
    if 'SSH_CONNECTION' not in os.environ:
        print('[!] Only SSH', file=sys.stderr)
        sys.exit(-1)

    logging.basicConfig(
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        filename = 'clig.log',
        level    = logging.DEBUG
        )

    os.chdir('repositories')

    CligShell()


class CligShell:
    def __init__(self):
        command = os.environ.get('SSH_ORIGINAL_COMMAND')
        if not command:
            print('No interactive shell access.', file=sys.stderr)
            sys.exit(-1)

        command = shlex.split(command)
        del os.environ['SSH_ORIGINAL_COMMAND']

        key_num = sys.argv[1]

        logging.info('%s: %s', key_num, command)

        fn = CligShell._commands.get(command[0])
        if not fn:
            print(f'[!] Error: Unknown command: {command[0]}', file=sys.stderr)
            sys.exit(-1)

        fn(self, *command)

    def _list(self, command, *repo):
        base = os.path.abspath('.')
        for root,directories,filenames in os.walk(base):
            for directory in directories:
                if directory.endswith('.git'):
                    name = os.path.join(root, directory)
                    name = name[len(base)+1:]
                    print(name)

    def _create(self, command, *repo):
        if not repo:
            print('[!] Error: Missing repository name')
            return

        repo = '/'.join(repo)
        if not repo.endswith('.git'):
            repo += '.git'

        #TODO: sanitize repo names
        self('git','init','--bare', repo)

    def _install(self, command):
        print('echo this could install clig')

    def _backup(self, *a):
        paths = []
        base = os.path.abspath('.')
        for root,directories,filenames in os.walk(base):
            for directory in directories:
                if directory.endswith('.git'):
                    name = os.path.join(root, directory)
                    name = name[len(base)+1:]
                    paths.append(name)

        args = ['tar', 'zcpf', '-'] + paths
        self(*args)

    def __call__(self, *command):
        p = subprocess.Popen(
            command,
            stdin  = sys.stdin.buffer,
            stdout = sys.stdout.buffer,
            )
        p.wait()

    _commands = {
        'list'               : _list,
        'create'             : _create,
        'install'            : _install,
        'backup'             : _backup,
        'git-upload-archive' : __call__,
        'git-upload-pack'    : __call__,
        'git-receive-pack'   : __call__,
        }
