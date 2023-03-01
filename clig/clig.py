#!/usr/bin/env python3

import sys
import os
import argparse
import shlex
import shutil
import subprocess
import time
import textwrap

DEFAULT_USER = 'clig'


class Clig:
    def __init__(self):
        if self.__doc__:
            description = textwrap.dedent(self.__doc__).strip()
        else:
            description = None

        # Top-level argument parser
        self.parser = argparse.ArgumentParser(
            description     = description,
            formatter_class = argparse.RawDescriptionHelpFormatter,
            )

        self.arguments()

        self.args,self.tailargs = self.parser.parse_known_args()

    def arguments(self):
        return

    def run(self):
        raise NotImplementedError

    def _call(self, command_line, *args, **kwds):
        if 'stdout' not in kwds:
            kwds['stdout'] = subprocess.PIPE
        if 'stderr' not in kwds:
            kwds['stderr'] = subprocess.STDOUT

        process = subprocess.Popen(
            shlex.split(command_line % args),
            **kwds
            )
        out,err = process.communicate()
        if out is not None:
            return out


class All(Clig):
    '''
    Apply a git command to all the repositories in the current directory
    '''
    def arguments(self):
        self.parser.add_argument('command', nargs='*', help='git command')

    def run(self):
        git_cmd = self.args.command + self.tailargs
        if not git_cmd:
            git_cmd = ['status', '-s']

        base = os.path.abspath('.')
        fmt = '-' * (shutil.get_terminal_size().columns)
        for root,directories,filenames in os.walk(base):
            directories.sort()
            filenames.sort()
            if '.git' not in directories and '.git' not in filenames:
                continue
            name = root[len(base)+1:]
            if name:
                sys.stdout.write('\x1b[34m')
                sys.stdout.write(fmt + '\r--- ')
                sys.stdout.write('\x1b[1;32m')
                sys.stdout.write(name)
                sys.stdout.write(' \x1b[0m\n')
            os.chdir(root)
            self._call('git %s', ' '.join(git_cmd), stdout=None, stderr=None)

class Create(Clig):
    '''
    Create a repository on the remote host
    '''
    def arguments(self):
        self.parser.add_argument('--user', '-u', default=DEFAULT_USER, help='Remote user')
        self.parser.add_argument('host',       help='Remote host')
        self.parser.add_argument('repository', help='Repository name')

    def run(self):
        out = self._call('ssh %s@%s create %s',
            self.args.user,
            self.args.host,
            self.args.repository,
            )
        sys.stdout.buffer.write(out)


class List(Clig):
    '''
    List all the repositories from the remote host
    '''
    def arguments(self):
        self.parser.add_argument('--user', '-u', default=DEFAULT_USER, help='Remote user')
        self.parser.add_argument('host', help='Remote host')

    def run(self):
        out = self._call('ssh %s@%s list',
            self.args.user,
            self.args.host,
            )
        sys.stdout.buffer.write(out)


class Tree(Clig):
    '''
    Clone all the repositories from the remote host
    '''
    def arguments(self):
        self.parser.add_argument('--user', '-u', default=DEFAULT_USER, help='Remote user')
        self.parser.add_argument('host', help='Remote host')
        self.parser.add_argument('filter', nargs='?', help='Remote host')

    def run(self):
        out = self._call('ssh %s@%s list',
            self.args.user,
            self.args.host,
            )
        repos = out.decode('utf-8').strip().split('\n')
        for repo in repos:
            if self.args.filter:
                if not repo.startswith(self.args.filter):
                    continue

            dest = repo
            if dest.endswith('.git'):
                dest = dest[:-4]

            args = '%s@%s:%s %s' % (self.args.user, self.args.host, repo, dest)
            print('[+]', dest)
            self._call('git clone %s', args, stdout = subprocess.DEVNULL)


class Backup(Clig):
    '''
    Create a backup of the remote repositories
    '''
    def arguments(self):
        self.parser.add_argument('--user', '-u', default=DEFAULT_USER, help='Remote user')
        self.parser.add_argument('host', help='Remote host')

    def run(self):
        path = 'git-%s-%s.tar.gz' % (self.args.host, time.strftime('%Y-%m-%d_%H%M%S'))
        with open(path, 'wb') as fp:
            tar = self._call('ssh %s@%s backup',
                self.args.user,
                self.args.host,
                stdout=fp
                )


def main():
    cmds = {
        'clig'       : All,
        'git-all'    : All,
        'git-backup' : Backup,
        'git-create' : Create,
        'git-list'   : List,
        'git-tree'   : Tree,
    }

    cmd = os.path.basename(sys.argv[0])
    # support installing
    if cmd == 'clig':
        if len(sys.argv) == 2:
            if sys.argv[1] == 'install':
                gitcmds = [k for k in cmds.keys() if k.startswith('git-')]
                gitcmds.sort()

                dirname = os.path.dirname(sys.argv[0])

                for gitcmd in gitcmds:
                    fullpath = os.path.join(dirname, gitcmd)
                    try:
                        os.symlink('clig', fullpath)
                        print(f'[+] Adding: {fullpath}')
                    except FileExistsError:
                        print(f'[+] Skipping: {fullpath}')
                    except Exception as e:
                        print(f'[!] Error: {fullpath}: {e}')
                return 0

    cls = cmds.get(cmd)
    if cls is None:
        sys.stderr.write('Unknown command: %s\n' % cmd)
        return -1

    return cls().run()
