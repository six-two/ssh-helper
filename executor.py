import subprocess
import os
import sys
# Local modules
from common import *

def execute_local_command(command, run_in_background=False, cwd=None):
    print_debug(command)
    options = {}
    options['cwd'] = cwd
    if run_in_background:
        options['stdout'] = subprocess.PIPE
        options['stderr'] = subprocess.STDOUT

    result = subprocess.run(command, **options)
    output = result.stdout if run_in_background else None
    r = (result.returncode, output)
    print_debug(r)
    return r


class Executor:
    def __init__(self, ssh_helper):
        self.local_path = None
        self.remote_path = None
        self.ssh_helper = ssh_helper

    def initialize(self):
        if not self.local_path:
            # Only run once
            print(f'Trying to login as "{self.ssh_helper.remote_username}@{self.ssh_helper.remote_host}"...')
            status, _ = self.execute_command(['echo', 'Login successful'], remote=True)
            if status != 0:
                print('\nFailed to login via ssh. See above error message for details')
                sys.exit(1)

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

    def complete_path(self, remote, allow_files, path_up_to_cursor, text):
        # #TODO improve option passing
        print_debug(f'[Complete path] remote={remote} "{path_up_to_cursor}" "{text}"')
        try:
            folder = os.path.dirname(path_up_to_cursor + 'handle_trailing_slash_correctly')
            if not folder:
                folder = '.'

            # TODO BUG this will likely break on special characters like \n, \t, etc in filenames
            ls_command = ['ls', '-1', '--escape', '--indicator-style=slash', '-A', '--color=never', folder]
            status, output = self.execute_command(ls_command, remote=remote, run_in_background=True)
            output = output.decode()
            if status != 0:
                print_debug(err(f'Error listing files in "{folder}": {output}'))
            else:
                matches = [file_name for file_name in output.split("\n") if file_name.startswith(text)]
                if not allow_files:
                    matches = [f for f in matches if f.endswith('/')]
                return matches
        except Exception as ex:
            pass  # TODO log these in a file somewhere?
            if DEBUG:
                print(ex)

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
        output = output.decode()
        if status != 0:
            print(output.strip())
            print(err('Process exited with code {}'.format(status)))
        # TODO only show useful columns
        output = output.split('\n', 1)[1]  # remove the 'total=...' line
        print(output)

    def cd(self, path, remote=False):
        if path:
            new_cwd = self.cwd(remote)
            new_cwd = os.path.join(new_cwd, path)
            new_cwd = os.path.normpath(new_cwd)
        else:
            new_cwd = self.default_remote_path if remote else self.default_local_path
        
        # Check if the target directory exists
        # TODO find a way that works. failed:(test, cd)
        status, _ = self.execute_command(['bash', '-c', f'cd \'{new_cwd}\''], remote=remote)
        if status == 0:
            if remote:
                self.remote_path = new_cwd
            else:
                self.local_path = new_cwd
        else:
            print(err('Not a valid directory or permission denied'))
