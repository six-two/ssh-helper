# pylint: disable=unused-wildcard-import
import subprocess
import os
import sys
import shlex
import re
from typing import Tuple, List, Sequence, Optional, Dict
# Local modules
from .common import *
from .ssh_utils import SshCommandBuilder, SshSettings


class CommandExecutionFailed(Exception):
    def __init__(self, command: Sequence[str], returncode: int):
        super().__init__(f'Command exited with non-zero status code ({returncode}):\n  "{shlex.join(command)}"')


def execute_in_background(command: Sequence[str], cwd: Optional[str]) -> str:
    result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        output = result.stdout.decode('utf-8')
    except:
        raise Exception(f'Command output is not vaild UTF-8: command={command}')

    if result.returncode != 0:
        print(err(output))
        raise CommandExecutionFailed(command, result.returncode)

    return output


def execute_in_foreground(command: Sequence[str], cwd: Optional[str]) -> None:
    result = subprocess.run(command, cwd=cwd)
    if result.returncode != 0:
        raise CommandExecutionFailed(command, result.returncode)


class Executor:
    def __init__(self, ssh_settings: SshSettings):
        self.ssh_helper = SshCommandBuilder(ssh_settings)
        self.default_local_path: Optional[str] = None
        self.default_remote_path: Optional[str] = None
        self.local_path: Optional[str] = None
        self.remote_path: Optional[str] = None

    def initialize(self):
        if not self.local_path:
            # Only run once
            print(f'Trying to login as "{self.ssh_helper.user_at_host}"...')
            try:
                self.execute(REMOTE, ['echo', 'Login successful'])
            except CommandExecutionFailed:
                print('\nFailed to login via ssh. See above error message for details')
                sys.exit(1)

            self.default_local_path = self.execute_in_background(LOCAL, ['pwd']).strip()
            self.default_remote_path = self.execute_in_background(REMOTE, ['pwd']).strip()

            self.local_path = self.default_local_path
            self.remote_path = self.default_remote_path

    def _prepare_command(self, is_remote: IsRemote, command: Sequence[str], ssh_options: Optional[Sequence[str]], shell: bool) -> Sequence[str]:
        if is_remote:
            if self.remote_path:
                command = ['cd', self.remote_path, ';', *command]
            if ssh_options is None:
                ssh_options = []
            return self.ssh_helper.make_remote_command(command, ssh_options=ssh_options)
        else:
            if shell:
                command = ['bash', '-c', shlex.join(command)]
            return command

    def execute_in_background(self, is_remote: IsRemote, command: Sequence[str], ssh_options: Sequence[str] = None, shell=False) -> str:
        c = self._prepare_command(is_remote, command, ssh_options, shell)
        return execute_in_background(c, self.local_path)

    def execute(self, is_remote: IsRemote, command: Sequence[str], ssh_options: Sequence[str] = None, shell=False) -> None:
        c = self._prepare_command(is_remote, command, ssh_options, shell)
        execute_in_foreground(c, self.local_path)

    def complete_path(self, remote: IsRemote, allow_files, path_up_to_cursor, text) -> List[str]:
        # #TODO improve option passing
        print_debug(f'[Complete path] remote={remote} "{path_up_to_cursor}" "{text}"')
        try:
            folder = os.path.dirname(path_up_to_cursor + 'handle_trailing_slash_correctly')
            if not folder:
                folder = '.'

            # TODO BUG this will likely break on special characters like \n, \t, etc in filenames
            ls_command = ['ls', '-1', '--escape', '--indicator-style=slash', '-A', '--color=never', folder]
            output = self.execute_in_background(remote, ls_command)
            matches = [file_name for file_name in output.split("\n") if file_name.startswith(text)]
            if not allow_files:
                matches = [f for f in matches if f.endswith('/')]
            return matches
        except CommandExecutionFailed as ex:
            print_debug(ex)
            return []
        except Exception as ex:
            # TODO log these in a file somewhere?
            print(err(str(ex)))
            return []

    def shell(self, is_remote: IsRemote, command_string: str = None):
        if command_string:
            # Execute the given command
            if is_remote:
                self.execute(REMOTE, shlex.split(command_string))
            else:
                self.execute(LOCAL, ['bash', '-c', command_string])
        else:
            # Open an interactive shell. "-t" enables the command prompts
            self.execute(is_remote, ['bash'], ssh_options=['-t'])

    def cwd(self, is_remote: IsRemote) -> Optional[str]:
        return self.remote_path if is_remote else self.local_path

    def ls(self, is_remote: IsRemote, path: str = None):
        command = ['ls', '-Alhb', '--time-style=long-iso', '--indicator-style=slash']
        if path:
            command += [path]

        output = self.execute_in_background(is_remote, command)
        lines = [l for l in output.split('\n') if l]
        # remove the 'total ...' line
        if len(lines) > 1 and lines[0].startswith('total'):
            lines = lines[1:]

        def remove_hard_link_count(line: str) -> str:
            try:
                rwx, _, the_rest = line.split(maxsplit=2)
                return f'{rwx} {the_rest}'
            except:
                return line

        lines = [remove_hard_link_count(l) for l in lines]
        # TODO only show useful columns
        print('\n'.join(lines))


    def cd(self, is_remote: IsRemote, path) -> None:
        if path:
            new_cwd = self.cwd(is_remote)
            new_cwd = os.path.join(new_cwd, path) if new_cwd else path
            new_cwd = os.path.normpath(new_cwd)
        else:
            new_cwd = self.default_remote_path if is_remote else self.default_local_path
        
        # Check if the target directory exists
        # TODO find a way that works. failed:(test, cd)
        try:
            self.execute(is_remote, ['bash', '-c', f'cd \'{new_cwd}\''])
            if is_remote:
                self.remote_path = new_cwd
            else:
                self.local_path = new_cwd
        except CommandExecutionFailed:
            print(err('Not a valid directory or permission denied'))

    # def get_vars(self, remote: IsRemote, variable_names) -> Dict[str, str]:
    #     output = self.execute_in_background(remote, ['printenv', variable_names], shell=True)
    #     values = output.split('\n')
    #     for name, value in zip(variable_names, values):
    #         pass

    def get_commands(self, remote: IsRemote, pattern: str = None) -> List[str]:
        # ['ls', '-1', '$PATH']
        path = self.execute_in_background(remote, ['printenv', 'PATH'])
        path_array = path.strip().split(':')
        output = self.execute_in_background(remote, ['ls', '-1', *path_array])
        commands = [line for line in output.split('\n') if line and not line.startswith('/')]
        # remove duplicates and sort alphabetical
        commands = sorted(set(commands))
        if pattern:
            regex = re.compile(pattern)
            commands = [c for c in commands if regex.search(c)]
        return commands

    def file_transfer(self, src: str, dst: str, is_upload: bool, is_directory: bool) -> None:
        command = self.ssh_helper.make_scp_command(src, dst, is_upload, is_directory)
        self.execute(LOCAL, command)
