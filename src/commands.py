# pylint: disable=unused-wildcard-import
import os
import re
from typing import List, Optional
# Local
from .common import *
from .my_shell import MyShell
from .command_builder import *
from .complete import *
from .my_decorators import make_command


def print_matching(lines: List[str], regex: Optional[str], fn_line_key: Callable[[str], str] = None) -> None:
    '''Basically this does what "grep" does'''
    lines = [l for l in lines if l]
    if regex is None:
        for l in lines:
            print(l)
    else:
        compiled_regex = re.compile(regex)
        for l in lines:
            key = fn_line_key(l) if fn_line_key else l
            print_debug(f'key: "{key}"')
            if compiled_regex.search(key):
                print(l)

@make_command(MyShell, 'Open a remote shell', 'r', raw_arg=True)
def shell(my_shell: MyShell, arg: str) -> None:
    '''If called without arguments, it will open a new interactive ssh session with the remote computer.
If called with a unix_command, it will run the unix_command on the remote machine.
You can also use "!" as an alias for this command.

Example:
- "shell" will open a remote interactive shell
- "!uname -a" will run "uname -a" on the remote computer'''
    my_shell.executor.shell(REMOTE, arg)

@make_command(MyShell, 'Open a local shell', 'l', raw_arg=True)
def lshell(my_shell: MyShell, arg: str) -> None:
    '''If called without arguments, it will open a new interactive shell on the local computer.
If called with arguments, it will run the arguments in a shell on the local machine'''
    my_shell.executor.shell(LOCAL, arg)

@make_command(MyShell, 'Enable/disable debugging')
def debug(my_shell: MyShell, enable: BoolOption) -> None:
    '''Enables / disables debugging output. This may interfere with some features like command completion'''
    set_debug(enable.value())
    print(f'Debug enabled: {enable.value()}')

@make_command(MyShell, 'Cause an error')
def error(my_shell: MyShell) -> None:
    '''Causes an internal error. Used to test exception handling'''
    raise Exception('Test exception')

@make_command(MyShell, 'Exit this shell', 'quit', 'EOF')
def exit(my_shell: MyShell) -> bool:
    '''Exit this interactive shell.
You can trigger this by pressing Ctrl-D on an empty prompt.'''
    return True

@make_command(MyShell, 'List remote files')
def ls(my_shell: MyShell, path: RFile = RFile('.')) -> None:
    '''List the files in the current directory or in the given path on the remote computer'''
    my_shell.executor.ls(REMOTE, '', path.value())

@make_command(MyShell, 'List local files')
def lls(my_shell: MyShell, path: LFile = LFile('.')) -> None:
    '''List the files in the current directory or in the given path on the local computer'''
    my_shell.executor.ls(LOCAL, '', path.value())

@make_command(MyShell, 'List local files')
def lls_format(my_shell: MyShell, flags: str, path: LFile = LFile('.')) -> None:
    '''List the files in the current directory or in the given path on the local computer'''
    my_shell.executor.ls(LOCAL, flags, path.value())


@make_command(MyShell, 'Print remote working directory')
def pwd(my_shell: MyShell) -> None:
    '''Show the full path of your current working directory on the remote computer'''
    my_shell.executor.execute(REMOTE, ['pwd'])

@make_command(MyShell, 'Print local working directory')
def lpwd(my_shell: MyShell) -> None:
    '''Show the full path of your current working directory on the local computer'''
    my_shell.executor.execute(LOCAL, 'pwd')

@make_command(MyShell, 'Delete a remote file')
def rm(my_shell: MyShell, path: RFile) -> None:
    '''Remove the file with the given path from the remote computer'''
    my_shell.executor.execute(REMOTE, ['rm', path.value()])

@make_command(MyShell, 'Delete a local file')
def lrm(my_shell: MyShell, path: LFile) -> None:
    '''Remove the file with the given path from the local computer'''
    my_shell.executor.execute(LOCAL, ['rm', path.value()])

@make_command(MyShell, 'Delete a remote folder')
def rmdir(my_shell: MyShell, path: RFolder) -> None:
    '''Remove the directory with the given path from the remote computer'''
    my_shell.executor.execute(REMOTE, ['rm', '-r', path.value()])

@make_command(MyShell, 'Delete a local folder')
def lrmdir(my_shell: MyShell, path: LFolder) -> None:
    '''Remove the directory with the given path from the local computer'''
    my_shell.executor.execute(LOCAL, ['rm', '-r', path.value()])

@make_command(MyShell, 'Change remote working directory')
def cd(my_shell: MyShell, path: RFolder = RFolder('')) -> None:
    '''If a path is given, the remote working directory is set to path.
If no path is given, the remote working directory is set to the users home directory.'''
    my_shell.executor.cd(REMOTE, path.value())

@make_command(MyShell, 'Change local working directory')
def lcd(my_shell: MyShell, path: LFolder = LFolder('')) -> None:
    '''If a path is given, the local working directory is set to path.
If no path is given, the local working directory is set to the users home directory.'''
    my_shell.executor.cd(LOCAL, path.value())

@make_command(MyShell, 'Download a remote file', 'dl')
def download(my_shell: MyShell, path: RFile) -> None:
    '''Download the file located at path from the local computer and saves it with the same filename in the working directory on the local computer.'''
    remote_path = path.value()
    local_path = os.path.basename(remote_path)
    is_upload = False
    is_directory = False
    my_shell.executor.file_transfer(remote_path, local_path, is_upload, is_directory)

@make_command(MyShell, 'Upload a local file', 'ul')
def upload(my_shell: MyShell, path: LFile) -> None:
    '''Upload the file located at path from the local computer and saves it with the same filename in the working directory on the remote computer.'''
    local_path = path.value()
    remote_path = os.path.basename(local_path)
    is_upload = True
    is_directory = False
    my_shell.executor.file_transfer(remote_path, local_path, is_upload, is_directory)

@make_command(MyShell, 'Edit a remote file', 'e')
def edit(my_shell: MyShell, path: RFile) -> None:
    '''Edit the file located at path on the remote computer'''
    my_shell.executor.execute(REMOTE, ['nano', path.value()])

@make_command(MyShell, 'Edit a local file', 'le')
def ledit(my_shell: MyShell, path: RFile) -> None:
    '''Edit the file located at path on the remote computer'''
    my_shell.executor.execute(LOCAL, ['nano', path.value()])

@make_command(MyShell, 'List/search remote commands', 'sc')
def search_commands(my_shell: MyShell, pattern: str = None) -> None:
    '''Lists all commands in the remote computers path, that match the regex.

Examples: 
- "sc ^php" will find all commands that start with "php"
- "sc admin" will find any commands that contain the word "admin"'''
    commands = my_shell.executor.all_commands(REMOTE)
    print_matching(commands, pattern)

@make_command(MyShell, 'List/search local commands', 'lsc')
def lsearch_commands(my_shell: MyShell, pattern: str = None) -> None:
    '''Lists all commands in the local computers path, that match the regex

Examples: 
- "sc ^php" will find all commands that start with "php"
- "sc admin" will find any commands that contain the word "admin"'''
    commands = my_shell.executor.all_commands(REMOTE)
    print_matching(commands, pattern)

@make_command(MyShell, 'test 123')
def test(my_shell: MyShell) -> None:
    '''Hello world

This text is multi-
line!'''
    print_debug('Debug is enabled\n')
    import inspect
    for member_name in sorted(dir(my_shell)):
        member = getattr(my_shell, member_name)
        if callable(member) and not member_name.startswith('__'):
            print(member_name, end='')
            try:
                print(inspect.signature(member))
            except:
                print(' <-- Could not determine signature')

@make_command(MyShell, 'Echos the path to a remote file')
def echo_rfile(my_shell: MyShell, path: RFile):
    print(f'Path: "{path.value()}"')

@make_command(MyShell, 'Execute a remote file')
def run(my_shell: MyShell, path: RFile) -> None:
    '''Mark the given file as executeable and then execute it'''
    lpath = os.path.join('.', path.value())
    chmod_and_exec = ['chmod', '+x', lpath, ';', lpath]
    my_shell.executor.execute(REMOTE, chmod_and_exec, shell=True)

@make_command(MyShell, 'Upload local file and execute on remote', 'upr')
def upload_and_run(my_shell: MyShell, path: LFile) -> None:
    '''Mark the given file as executeable and then execute it'''
    file_name = RFile(os.path.basename(path.value()))

    upload(my_shell, path)
    run(my_shell, file_name)

@make_command(MyShell, 'Print remote variables', 'sv')
def search_vars(my_shell: MyShell, regex: str = None) -> None:
    '''Without arguments: Prints all remote variables.
With argument: Only variables that contain pattern'''
    env_vars = my_shell.executor.execute_in_background(REMOTE, ['printenv']).split('\n')
    print_matching(env_vars, regex, lambda l: l.split('=')[0])

@make_command(MyShell, 'Print local variables', 'lsv')
def lsearch_vars(my_shell: MyShell, regex: str = None) -> None:
    '''Without arguments: Prints all local variables.
With argument: Only variables that contain pattern'''
    env_vars = my_shell.executor.execute_in_background(LOCAL, ['printenv']).split('\n')
    print_matching(env_vars, regex, lambda l: l.split('=')[0])