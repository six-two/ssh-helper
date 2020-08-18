# pylint: disable=unused-wildcard-import
import subprocess
import os
import sys
import shlex
from typing import Tuple, List, Sequence, Optional
# Local modules
from common import *
from ssh_command_builder import SshCommandConverter


def execute_local_command(command: Sequence[str], run_in_background: bool = False, cwd: str = None) -> Tuple[int, bytes]:
    try:
        print_debug(command)
        stdout = subprocess.PIPE if run_in_background else None
        stderr = subprocess.STDOUT if run_in_background else None
        result = subprocess.run(command, cwd=cwd, stdout=stdout, stderr=stderr)

        output = result.stdout if run_in_background else b'Output is only captured when run_in_background is True'
        r = (result.returncode, output)
        print_debug(r)
        return r
    except Exception as ex:
        print(err(f'Failed to execute command {command}:'))
        print(err(str(ex)))
        return (-1, f'Failed to execute command {command}'.encode())


class Executor:
    def __init__(self, ssh_helper):
        self.local_path = None
        self.remote_path = None
        self.ssh_helper = ssh_helper

    def initialize(self):
        if not self.local_path:
            # Only run once
            print(f'Trying to login as "{self.ssh_helper.user_at_host}"...')
            status, _ = self.execute_command(REMOTE, ['echo', 'Login successful'])
            if status != 0:
                print('\nFailed to login via ssh. See above error message for details')
                sys.exit(1)

            self.local_path = self.default_local_path = self.pwd(LOCAL, run_in_background=True)
            self.remote_path = self.default_remote_path = self.pwd(REMOTE, run_in_background=True)

    def execute_command(self, is_remote: IsRemote, command: Sequence[str], run_in_background=False, ssh_options=[]) -> Tuple[int, bytes]:
        if is_remote:
            if self.remote_path:
                command = ['cd', self.remote_path, ';', *command]
            command = self.ssh_helper.make_remote_command(command, ssh_options=ssh_options)
        return execute_local_command(command,
                                    run_in_background=run_in_background,
                                    cwd=self.local_path)

    def complete_path(self, remote: IsRemote, allow_files, path_up_to_cursor, text):
        # #TODO improve option passing
        print_debug(f'[Complete path] remote={remote} "{path_up_to_cursor}" "{text}"')
        try:
            folder = os.path.dirname(path_up_to_cursor + 'handle_trailing_slash_correctly')
            if not folder:
                folder = '.'

            # TODO BUG this will likely break on special characters like \n, \t, etc in filenames
            ls_command = ['ls', '-1', '--escape', '--indicator-style=slash', '-A', '--color=never', folder]
            status, output_bytes = self.execute_command(remote, ls_command, run_in_background=True)
            output = output_bytes.decode()
            if status != 0:
                print_debug(err(f'Error listing files in "{folder}": {output}'))
            else:
                matches = [file_name for file_name in output.split("\n") if file_name.startswith(text)]
                if not allow_files:
                    matches = [f for f in matches if f.endswith('/')]
                return matches
        except Exception as ex:
            # TODO log these in a file somewhere?
            print_debug(ex)

    def shell(self, is_remote: IsRemote, command_string: str = None):
        if command_string:
            # Execute the given command
            command = shlex.split(command_string)
            self.execute_command(is_remote, command)
        else:
            # Open an interactive shell. "-t" enables the command prompts
            self.execute_command(is_remote, ['bash'], ssh_options=['-t'])

    def pwd(self, is_remote: IsRemote, run_in_background=False):
        # Todo: add error handling? Add remote timeouts?
        status, output = self.execute_command(is_remote, ["pwd"], run_in_background=run_in_background)
        if status != 0:
            raise Exception('Process exited with code {}'.format(status))
        if run_in_background:
            return output.decode().strip()

    def cwd(self, is_remote: IsRemote):
        return self.remote_path if is_remote else self.local_path

    def ls(self, is_remote: IsRemote, path: str = None):
        command = ['ls', '-Alg']
        if path:
            command += [path]

        status, output_bytes = self.execute_command(is_remote, command, run_in_background=True)
        output = output_bytes.decode()
        if status != 0:
            print(output.strip())
            print(err('Process exited with code {}'.format(status)))
        # TODO only show useful columns
        output = output.split('\n', 1)[1]  # remove the 'total=...' line
        print(output)

    def cd(self, is_remote: IsRemote, path):
        if path:
            new_cwd = self.cwd(is_remote)
            new_cwd = os.path.join(new_cwd, path)
            new_cwd = os.path.normpath(new_cwd)
        else:
            new_cwd = self.default_remote_path if is_remote else self.default_local_path
        
        # Check if the target directory exists
        # TODO find a way that works. failed:(test, cd)
        status, _ = self.execute_command(is_remote, ['bash', '-c', f'cd \'{new_cwd}\''])
        if status == 0:
            if is_remote:
                self.remote_path = new_cwd
            else:
                self.local_path = new_cwd
        else:
            print(err('Not a valid directory or permission denied'))

    def file_transfer(self, src: str, dst: str, is_upload: bool, is_directory: bool):
        command = self.ssh_helper.make_scp_command(src, dst, is_upload, is_directory)
        self.execute_command(LOCAL, command)
