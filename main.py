#!/usr/bin/env python3
import subprocess
import os
import cmd
from termcolor import colored

DEBUG = False
NAME = 'Dummie{}ell'.format(colored('SSH', 'red'))
HELP_TIP = 'Type "help" or "?" to list commands.'
USAGE = """
ssh-helper

Some commands can be executed on either localy or remotely. They are prefixed with a "(l)" like in "(l)pwd".
In this case use "pwd" to execute the command on the remote machine, use "lpwd" to execute the command on the local machine
Other conventions: 
  <mandatory_argument>
  [optional argument]
  use_either_this_command | or_use_this_one

Commands:
(l)pwd          | Print the working directory's path
(l)ls [path]    | Lists all files and directories in the working directory (or path if supplied)
(l)cd [path]    | Change the working directory (to path if supplied, otherwise to the users home directory)
help | ?        | Show this help message
help | ? [cmd]  | Shows help about the given command
shell | !       | Opens an interactive ssh session. Exit it as usual (via "exit" or Ctrl-D)
shell | ! [cmd] | The given command will be run in a shell on the remote machine
"""


class SshCommandConverter:
    def __init__(self, remote_host, remote_user, remote_password=None):
        self.remote_username = remote_user
        self.remote_password = remote_password
        self.remote_host = remote_host

    def make_remote_command(self, command, ssh_options=[]):
        complete_command = []
        if self.remote_password:
            complete_command += ['sshpass', '-p', self.remote_password]

        ssh_user = '{}@{}'.format(self.remote_username, self.remote_host)
        complete_command += ['ssh', *ssh_options, ssh_user]
        complete_command += command
        return complete_command

    def make_scp_command(self, src, dst, is_upload, is_directory):
        remote_prefix = '{}@{}:'.format(self.remote_username, self.remote_host)
        if is_upload:
            dst = remote_prefix + dst
        else:
            src = remote_prefix + src

        complete_command = []
        if self.remote_password:
            complete_command += ['sshpass', '-p', self.remote_password]

        complete_command += ['scp', '-p']
        if is_directory:
            complete_command += ['-r']
        complete_command += [src, dst]


def execute_local_command(command, run_in_background=False, cwd=None):
    if DEBUG:
        print(command)
    options = {}
    options['cwd'] = cwd
    if run_in_background:
        options['stdout'] = subprocess.PIPE
        options['stderr'] = subprocess.STDOUT

    result = subprocess.run(command, **options)
    output = result.stdout if run_in_background else None
    r = (result.returncode, output)
    if DEBUG:
        print(r)
    return r


class Executor:
    def __init__(self, remote_host, remote_user, remote_password=None):
        self.local_path = None
        self.remote_path = None
        self.ssh_helper = SshCommandConverter(remote_host, remote_user, remote_password)

        self.local_path = self.default_local_path = self.pwd(run_in_background=True)
        self.remote_path = self.default_remote_path = self.pwd(run_in_background=True, remote=True)

    def execute_command(self, command, remote=False, run_in_background=False, ssh_options=[]):
        if remote:
            if self.remote_path:
                command = ['cd', self.remote_path, ';'] + command
            command = self.ssh_helper.make_remote_command(command, ssh_options=ssh_options)
        return execute_local_command(command,
                                     run_in_background=run_in_background,
                                     cwd=self.local_path)

    def shell(self, command=None):
        if command:
            # Execute the given command in a shell
            # self.execute_command(['bash', '-c', command], remote=True)
            self.execute_command([command], remote=True)
        else:
            # Open an interactive shell. "-t" enables the command prompts
            self.execute_command(['bash'], remote=True, ssh_options=['-t'])

    def pwd(self, remote=False, run_in_background=False):
        # Todo: add error handling? Add remote timeouts?
        status, output = self.execute_command(["pwd"], remote=remote, run_in_background=run_in_background)
        if status != 0:
            raise Exception('Process exited with code {}'.format(status))
        if run_in_background:
            return output.decode().strip()

    def cwd(self, remote=False):
        return self.remote_path if remote else self.local_path

    def ls(self, path=None, remote=False):
        command = ['ls', '-Alg']
        if path:
            command += [path]

        status, output = self.execute_command(command, remote=remote, run_in_background=True)
        if status != 0:
            raise Exception('Process exited with code {}'.format(status))
        # TODO only show useful columns
        output = output.decode()
        output = output.split('\n', 1)[1]  # remove the 'total=...' line
        print(output)

    def cd(self, path, remote=False):
        if path:
            new_cwd = self.cwd(remote)
            new_cwd = os.path.join(new_cwd, path)
            new_cwd = os.path.normpath(new_cwd)
        else:
            new_cwd = self.default_remote_path if remote else self.default_local_path

        if remote:
            self.remote_path = new_cwd
        else:
            self.local_path = new_cwd


class MyShell(cmd.Cmd):
    intro = f'Welcome to the {NAME}. {HELP_TIP}\n'
    prompt = '(cmd) '

    def __init__(self, executor):
        super().__init__()
        self.executor = executor

    def default(self, line):
        print(colored('Unknown command: "{}"', 'red').format(line.split()[0]))
        print(HELP_TIP)

    def do_EOF(self, arg):
        'Exit this shell by pressing Ctrl-D on an empty prompt'
        return True

    def do_exit(self, arg):
        'Exit this interactive shell'
        return True

    def do_shell(self, arg):
        'If called without arguments it will open a new interactive ssh session. If called with argument(s) it will run the argument(s) as a command on the remote machine and then'
        print(f'Got command: "{arg}"')
        self.executor.shell(arg)

    def do_help(self, arg):
        if not arg:
            print(USAGE)
        else:
            super().do_help(arg)

    def help_help(self):
        print('You can use the help command to show what commands are available and what they do')

if __name__ == '__main__':
    import sys
    if "-h" in sys.argv or "--help" in sys.argv:
        print(USAGE)
        sys.exit()

    # Default settings for metasploitable 3 (ubuntu 14.04)
    i = Executor("172.28.128.3", "vagrant", "vagrant")
    s = MyShell(i)
    try:
        s.cmdloop()
    except KeyboardInterrupt:
        pass

    # i.remote_path = "/home"
    # i.ls(remote=True)
    # i.local_path = "/home"
    # i.ls()
    # i.ls("/tmp")
