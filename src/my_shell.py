# pylint: disable=unused-wildcard-import
import cmd
import os
from typing import List
import re
# Local modules
from common import *
from executor import Executor
from ssh_command_builder import SshSettings
from my_decorators import *
# External libraries. Might need no be installed via pip
import termcolor


NAME = 'Dummie{}ell'.format(termcolor.colored('SSH', 'red'))
HELP_TIP = 'Type "help" or "?" to list commands.'
USAGE = """
ssh-helper

Some commands can be executed on either localy or remotely. They are prefixed with a "(l)" like in "(l)pwd".
In this case use "pwd" to execute the command on the remote machine, use "lpwd" to execute the command on the local machine
Other conventions: 
  <mandatory_argument>
  [optional_argument]
  (use_either_this_command | or_use_this_one)

Commands:
d                | Enable debug mode
(l)pwd           | Print the working directory's path
(l)ls [path]     | Lists all files and directories in the working directory (or path if supplied)
(l)cd [path]     | Change the working directory (to path if supplied, otherwise to the users home directory)
(help | ?)       | Show this help message
(help | ?) <cmd> | Shows help about the given command
(shell | !)      | Opens an interactive ssh session. Exit it as usual (via "exit" or Ctrl-D)
(shell | !) <cmd>| The given command will be run in a shell on the remote machine
"""

def get_available_commands():
    commands = []
    usage_start = 'Usage: '
    alias_regex = re.compile(r'\((.*?) \| (.*?)\) (.*)')
    for member_name in dir(MyShell):
        member = getattr(MyShell, member_name)
        if member_name.startswith('do_') and callable(member):
            usage = member.__doc__.split('\n')[0]
            if usage.startswith(usage_start):
                usage = usage[len(usage_start):]
                result = alias_regex.match(usage)
                if result:
                    name, alias, arguments = result.groups()
                    commands += [f'{name} {arguments}', f'{alias} {arguments}']
                else:
                    commands.append(usage)
            else:
                print(f'[Warning] Bad usage format: "{usage}"')

    return sorted(commands)


@decorate_all_methods_starting_with(print_exceptions, ['do_', 'complete_', 'help_'])
class MyShell(cmd.Cmd):
    intro = f'Welcome to the {NAME}. {HELP_TIP}\n'

    def __init__(self, ssh_settings: SshSettings) -> None:
        super().__init__()
        self.executor = Executor(ssh_settings)
        self.prompt = '(You should not see this message)'

        # def signal_handler(sig, frame):
        #     print('You pressed Ctrl+C!')
            
        # signal.signal(signal.SIGINT, signal_handler)


    def preloop(self) -> None:
        self.executor.initialize()
        self.update_prompt()

    def complete_path_single_argument(self, remote: IsRemote, allow_files: bool, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        line_before_cursor = line[:endidx]
        command, argument_before_cursor = line_before_cursor.split(' ', 1)
        print_debug(f'Single arg complete for "{command}"')
        return self.executor.complete_path(remote, allow_files, argument_before_cursor, text)

    def precmd(self, line: str) -> str:
        # try to replace 'l!' with 'lshell'
        l = line.lstrip()
        if l.startswith("l!"):
            line = f'lshell {l[2:]}'

        return line

    def postcmd(self, stop: bool, line: str) -> bool:
        '''Update the prompt after running a command'''
        self.update_prompt()
        return stop

    def update_prompt(self) -> None:
        remote_dirname = os.path.basename(self.executor.remote_path)
        prompt = f'({remote_dirname}) '
        self.prompt = termcolor.colored(prompt, 'blue')

    def default(self, line: str) -> bool:
        '''Executed if the user input matches no defined command'''
        command = line.split()[0]
        print(err(f'Unknown command: "{command}"'))
        print(HELP_TIP)
        return False

    @no_args
    def do_EOF(self, arg: str) -> bool:
        '''Usage: EOF
Exit this shell. You can also trigger this by pressing Ctrl-D on an empty prompt'''
        return True

    @no_args
    def do_exit(self, arg: str) -> bool:
        '''Usage: exit
Exit this interactive shell'''
        return True

    def do_shell(self, arg: str) -> None:
        '''Usage: (shell | !) [unix_command]
If called without arguments, it will open a new interactive ssh session with the remote computer.
If called with a unix_command, it will run the unix_command on the remote machine'''
        self.executor.shell(REMOTE, arg)

    def do_lshell(self, arg: str) -> None:
        '''Usage: (lshell | l!) [unix_command]
If called without arguments, it will open a new interactive shell on the local computer.
If called with a unix_command, it will run the unix_command on the local machine'''
        self.executor.shell(LOCAL, arg)

    def do_help(self, arg: str) -> None:
        '''Usage: (help | ?) [command]
If command is given, a help message about the command will be shown.
Otherwise a list of valid commands and their usage is displayed'''
        if not arg:
            print("Available commands:")
            for command in get_available_commands():
                print(f'  {command}')
        else:
            super().do_help(arg)

    @no_args
    def do_dbg(self, arg: str) -> None:
        '''Usage: dbg
Enables debugging output. This may interfere with some features like command completion'''
        set_debug(True)
        print("Debug mode enabled!")

    @no_args
    def do_error(self, arg: str) -> None:
        '''Usage: error
Causes an internal error. Used to test exception handling'''
        raise Exception('Test exception')

# ======================= (l)ls =======================
    def do_ls(self, arg: str) -> None:
        '''Usage: ls [path]
List the files in the current directory or in the given path on the remote computer'''
        self.executor.ls(REMOTE, arg)

    def complete_ls(self, *args) -> List[str]:
        return self.complete_path_single_argument(REMOTE, True, *args)

    def do_lls(self, arg: str) -> None:
        '''Usage: lls [path]
List the files in the current directory or in the given path on the local computer'''
        self.executor.ls(LOCAL, arg)

    def complete_lls(self, *args) -> List[str]:
        return self.complete_path_single_argument(LOCAL, True, *args)

# ======================= (l)pwd =======================

    @no_args
    def do_pwd(self, arg: str) -> None:
        '''Usage: pwd
Show the full path of your current working directory on the remote computer'''
        self.executor.pwd(REMOTE)

    @no_args
    def do_lpwd(self, arg: str) -> None:
        '''Usage: lpwd
Show the full path of your current working directory on the local computer'''
        self.executor.pwd(LOCAL)

# ======================= (l)cd =======================
    def do_cd(self, arg: str) -> None:
        '''Usage: cd [path]
If a path is given, the remote working directory is set to path.
If no path is given, the remote working directory is set to the users home directory.'''
        self.executor.cd(REMOTE, arg)

    def complete_cd(self, *args) -> List[str]:
        return self.complete_path_single_argument(REMOTE, False, *args)

    def do_lcd(self, arg: str) -> None:
        '''Usage: lcd [path]
If a path is given, the local working directory is set to path.
If no path is given, the local working directory is set to the users home directory.'''
        self.executor.cd(LOCAL, arg)

    def complete_lcd(self, *args) -> List[str]:
        return self.complete_path_single_argument(LOCAL, False, *args)

# ======================= download =======================
    def do_download(self, arg: str) -> None:
        '''Usage: download <path>
Download the file located at path from the local computer and saves it with the same filename in the working directory on the local computer.'''
        remote_path = arg
        local_path = os.path.basename(remote_path)
        is_upload = False
        is_directory = False
        self.executor.file_transfer(remote_path, local_path, is_upload, is_directory)

    def complete_download(self, *args) -> List[str]:
        return self.complete_path_single_argument(REMOTE, True, *args)

    def do_upload(self, arg: str) -> None:
        '''Usage: upload <path>
Upload the file located at path from the local computer and saves it with the same filename in the working directory on the remote computer.'''
        local_path = arg
        remote_path = os.path.basename(local_path)
        is_upload = True
        is_directory = False
        self.executor.file_transfer(remote_path, local_path, is_upload, is_directory)

    def complete_upload(self, *args) -> List[str]:
        return self.complete_path_single_argument(LOCAL, True, *args)
