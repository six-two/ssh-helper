# pylint: disable=unused-wildcard-import
import cmd
import os
from typing import List
import re
# Local modules
from .common import *
from .executor import Executor
from .ssh_utils import SshSettings
from .my_decorators import *
# External libraries. Might need no be installed via pip
import termcolor


NAME = 'Dummie{}ell'.format(termcolor.colored('SSH', 'red'))
HELP_TIP = 'Type "help" or "?" to list commands.'

def get_available_commands() -> List[str]:
    commands = []
    alias_regex = re.compile(r'\((.*?) \| (.*?)\) (.*)')
    for member_name in dir(MyShell):
        member = getattr(MyShell, member_name)
        if member_name.startswith('do_') and callable(member):
            usage = get_usage(member)
            if usage:
                result = alias_regex.match(usage)
                if result:
                    name, alias, arguments = result.groups()
                    commands += [f'{name} {arguments}', f'{alias} {arguments}']
                else:
                    commands.append(usage)

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
        if self.executor.remote_path:
            remote_dirname = os.path.basename(self.executor.remote_path)
            prompt = f'({remote_dirname}) '
            self.prompt = termcolor.colored(prompt, 'blue')

    def default(self, line: str) -> bool:
        '''Executed if the user input matches no defined command'''
        command = line.split()[0]
        print(err(f'Unknown command: "{command}"'))
        print(HELP_TIP)
        return False

    @arg_count(0)
    def do_EOF(self) -> bool:
        '''Usage: EOF
Exit this shell. You can also trigger this by pressing Ctrl-D on an empty prompt'''
        return True

    @arg_count(0)
    def do_exit(self) -> bool:
        '''Usage: exit
Exit this interactive shell'''
        return True

    # No decorator, so that we can pass the raw string through
    def do_shell(self, arg: str) -> None:
        '''Usage: (shell | !) [unix_command]
If called without arguments, it will open a new interactive ssh session with the remote computer.
If called with a unix_command, it will run the unix_command on the remote machine'''
        self.executor.shell(REMOTE, arg)

    # No decorator, so that we can pass the raw string through
    def do_lshell(self, arg: str) -> None:
        '''Usage: (lshell | l!) [unix_command]
If called without arguments, it will open a new interactive shell on the local computer.
If called with a unix_command, it will run the unix_command on the local machine'''
        self.executor.shell(LOCAL, arg)

    @arg_count(0, 1)
    def do_help(self, arg: str = None) -> None:
        '''Usage: (help | ?) [command]
If command is given, a help message about the command will be shown.
Otherwise a list of valid commands and their usage is displayed'''
        if not arg:
            print("Available commands:")
            for command in get_available_commands():
                print(f'  {command}')
        else:
            # Work around for '??'
            if arg == '?':
                arg = 'help'
            super().do_help(arg)

    @arg_count(1)
    def do_debug(self, value: str) -> None:
        '''Usage: debug <on | off>
Enables / disables debugging output. This may interfere with some features like command completion'''
        if value == 'on':
            set_debug(True)
            print("Debug mode enabled!")
        elif value == 'off':
            set_debug(False)
            print("Debug mode disabled!")
        else:
            print_usage(self.do_debug)

    @arg_count(0)
    def do_error(self) -> None:
        '''Usage: error
Causes an internal error. Used to test exception handling'''
        raise Exception('Test exception')

# ======================= (l)ls =======================
    @arg_count(0, 1)
    def do_ls(self, path: str = None) -> None:
        '''Usage: ls [path]
List the files in the current directory or in the given path on the remote computer'''
        self.executor.ls(REMOTE, path)

    def complete_ls(self, *args) -> List[str]:
        return self.complete_path_single_argument(REMOTE, True, *args)

    @arg_count(0, 1)
    def do_lls(self, path: str = None) -> None:
        '''Usage: lls [path]
List the files in the current directory or in the given path on the local computer'''
        self.executor.ls(LOCAL, path)

    def complete_lls(self, *args) -> List[str]:
        return self.complete_path_single_argument(LOCAL, True, *args)

# ======================= (l)pwd =======================
    @arg_count(0)
    def do_pwd(self) -> None:
        '''Usage: pwd
Show the full path of your current working directory on the remote computer'''
        self.executor.execute(REMOTE, ['pwd'])

    @arg_count(0)
    def do_lpwd(self) -> None:
        '''Usage: lpwd
Show the full path of your current working directory on the local computer'''
        self.executor.execute(LOCAL, 'pwd')

# ======================= (l)rm =======================
    @arg_count(1)
    def do_rm(self, path: str) -> None:
        '''Usage: rm <path>
Remove the file with the given path from the remote computer'''
        self.executor.execute(REMOTE, ['rm', path])

    def complete_rm(self, *args) -> List[str]:
        return self.complete_path_single_argument(REMOTE, True, *args)

    @arg_count(1)
    def do_lrm(self, path: str) -> None:
        '''Usage: lrm <path>
Remove the file with the given path from the local computer'''
        self.executor.execute(LOCAL, ['rm', path])

    def complete_lrm(self, *args) -> List[str]:
        return self.complete_path_single_argument(LOCAL, True, *args)

# ======================= (l)rmdir =======================
    @arg_count(1)
    def do_rmdir(self, path: str) -> None:
        '''Usage: rmdir <path>
Remove the directory with the given path from the remote computer'''
        self.executor.execute(REMOTE, ['rm', '-r', path])

    def complete_rmdir(self, *args) -> List[str]:
        return self.complete_path_single_argument(REMOTE, True, *args)

    @arg_count(1)
    def do_lrmdir(self, path: str) -> None:
        '''Usage: lrmdir <path>
Remove the directory with the given path from the local computer'''
        self.executor.execute(LOCAL, ['rm', '-r', path])

    def complete_lrmdir(self, *args) -> List[str]:
        return self.complete_path_single_argument(LOCAL, True, *args)


# ======================= (l)cd =======================
    @arg_count(0, 1)
    def do_cd(self, path: str = None) -> None:
        '''Usage: cd [path]
If a path is given, the remote working directory is set to path.
If no path is given, the remote working directory is set to the users home directory.'''
        self.executor.cd(REMOTE, path)

    def complete_cd(self, *args) -> List[str]:
        return self.complete_path_single_argument(REMOTE, False, *args)

    @arg_count(0, 1)
    def do_lcd(self, path: str = None) -> None:
        '''Usage: lcd [path]
If a path is given, the local working directory is set to path.
If no path is given, the local working directory is set to the users home directory.'''
        self.executor.cd(LOCAL, path)

    def complete_lcd(self, *args) -> List[str]:
        return self.complete_path_single_argument(LOCAL, False, *args)

# ======================= download =======================
    @arg_count(1)
    def do_download(self, path: str) -> None:
        '''Usage: download <path>
Download the file located at path from the local computer and saves it with the same filename in the working directory on the local computer.'''
        remote_path = path
        local_path = os.path.basename(remote_path)
        is_upload = False
        is_directory = False
        self.executor.file_transfer(remote_path, local_path, is_upload, is_directory)

    def complete_download(self, *args) -> List[str]:
        return self.complete_path_single_argument(REMOTE, True, *args)

# ======================= upload =======================
    @arg_count(1)
    def do_upload(self, path: str) -> None:
        '''Usage: upload <path>
Upload the file located at path from the local computer and saves it with the same filename in the working directory on the remote computer.'''
        local_path = path
        remote_path = os.path.basename(local_path)
        is_upload = True
        is_directory = False
        self.executor.file_transfer(remote_path, local_path, is_upload, is_directory)

    def complete_upload(self, *args) -> List[str]:
        return self.complete_path_single_argument(LOCAL, True, *args)

# ======================= edit =======================
    @arg_count(1)
    def do_edit(self, path: str) -> None:
        '''Usage: edit <path>
Edit the file located at path on the remote computer'''
        self.executor.execute(REMOTE, ['nano', path])

    def complete_edit(self, *args) -> List[str]:
        return self.complete_path_single_argument(LOCAL, True, *args)
