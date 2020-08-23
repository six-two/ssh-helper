# pylint: disable=unused-wildcard-import
import os
# Local
from .common import *
from .my_shell import MyShell
from .command_builder import *
from .complete import *
from .my_decorators import make_command


@make_command(MyShell, 'Open a remote shell', 'shell', 'r', raw_arg=True)
def shell(my_shell: MyShell, arg: str) -> None:
    '''If called without arguments, it will open a new interactive ssh session with the remote computer.
If called with a unix_command, it will run the unix_command on the remote machine.
You can also use "!" as an alias for this command.

Example:
- "shell" will open a remote interactive shell
- "!uname -a" will run "uname -a" on the remote computer'''
    my_shell.executor.shell(REMOTE, arg)

@make_command(MyShell, 'Open a local shell', 'lshell', 'l', raw_arg=True)
def lshell(my_shell: MyShell, arg: str) -> None:
    '''If called without arguments, it will open a new interactive shell on the local computer.
If called with arguments, it will run the arguments in a shell on the local machine'''
    my_shell.executor.shell(LOCAL, arg)

@make_command(MyShell, 'Enable/disable debugging', 'debug')
def debug(my_shell: MyShell, enable: BoolOption) -> None:
    '''Enables / disables debugging output. This may interfere with some features like command completion'''
    set_debug(enable.value())
    print(f'Debug enabled: {enable.value()}')

@make_command(MyShell, 'Cause an error', 'error')
def error(my_shell: MyShell) -> None:
    '''Causes an internal error. Used to test exception handling'''
    raise Exception('Test exception')

@make_command(MyShell, 'Exit this shell', 'exit', 'quit', 'EOF')
def exit(my_shell: MyShell) -> bool:
    '''Exit this interactive shell.
You can trigger this by pressing Ctrl-D on an empty prompt.'''
    return True

@make_command(MyShell, 'List remote files', 'ls')
def ls(my_shell: MyShell, path: str = None) -> None:
    '''List the files in the current directory or in the given path on the remote computer'''
    my_shell.executor.ls(REMOTE, path)

@make_command(MyShell, 'List local files', 'lls')
def lls(my_shell: MyShell, path: str = None) -> None:
    '''List the files in the current directory or in the given path on the local computer'''
    my_shell.executor.ls(LOCAL, path)

@make_command(MyShell, 'Print remote working directory', 'pwd')
def pwd(my_shell: MyShell) -> None:
    '''Show the full path of your current working directory on the remote computer'''
    my_shell.executor.execute(REMOTE, ['pwd'])

@make_command(MyShell, 'Print local working directory', 'lpwd')
def lpwd(my_shell: MyShell) -> None:
    '''Show the full path of your current working directory on the local computer'''
    my_shell.executor.execute(LOCAL, 'pwd')

@make_command(MyShell, 'Delete a remote file', 'rm')
def rm(my_shell: MyShell, path: str) -> None:
    '''Remove the file with the given path from the remote computer'''
    my_shell.executor.execute(REMOTE, ['rm', path])

@make_command(MyShell, 'Delete a local file', 'lrm')
def lrm(my_shell: MyShell, path: str) -> None:
    '''Remove the file with the given path from the local computer'''
    my_shell.executor.execute(LOCAL, ['rm', path])

@make_command(MyShell, 'Delete a remote folder', 'rmdir')
def rmdir(my_shell: MyShell, path: str) -> None:
    '''Remove the directory with the given path from the remote computer'''
    my_shell.executor.execute(REMOTE, ['rm', '-r', path])

@make_command(MyShell, 'Delete a local folder', 'lrmdir')
def lrmdir(my_shell: MyShell, path: str) -> None:
    '''Remove the directory with the given path from the local computer'''
    my_shell.executor.execute(LOCAL, ['rm', '-r', path])

@make_command(MyShell, 'Change remote working directory', 'cd')
def cd(my_shell: MyShell, path: str = None) -> None:
    '''If a path is given, the remote working directory is set to path.
If no path is given, the remote working directory is set to the users home directory.'''
    my_shell.executor.cd(REMOTE, path)

@make_command(MyShell, 'Change local working directory', 'lcd')
def lcd(my_shell: MyShell, path: str = None) -> None:
    '''If a path is given, the local working directory is set to path.
If no path is given, the local working directory is set to the users home directory.'''
    my_shell.executor.cd(LOCAL, path)

@make_command(MyShell, 'Download a remote file', 'download')
def download(my_shell: MyShell, path: str) -> None:
    '''Download the file located at path from the local computer and saves it with the same filename in the working directory on the local computer.'''
    remote_path = path
    local_path = os.path.basename(remote_path)
    is_upload = False
    is_directory = False
    my_shell.executor.file_transfer(remote_path, local_path, is_upload, is_directory)

@make_command(MyShell, 'Upload a local file', 'upload')
def upload(my_shell: MyShell, path: str) -> None:
    '''Upload the file located at path from the local computer and saves it with the same filename in the working directory on the remote computer.'''
    local_path = path
    remote_path = os.path.basename(local_path)
    is_upload = True
    is_directory = False
    my_shell.executor.file_transfer(remote_path, local_path, is_upload, is_directory)

@make_command(MyShell, 'Edit a remote file', 'edit')
def edit(my_shell: MyShell, path: str) -> None:
    '''Edit the file located at path on the remote computer'''
    my_shell.executor.execute(REMOTE, ['nano', path])

@make_command(MyShell, 'List/search remote commands', 'search-command', 'sc')
def sc(my_shell: MyShell, pattern: str = None) -> None:
    '''Lists all commands in the remote computers path, that match the regex.

Examples: 
- "sc ^php" will find all commands that start with "php"
- "sc admin" will find any commands that contain the word "admin"'''
    commands = my_shell.executor.get_commands(REMOTE, pattern)
    print('\n'.join(commands))

@make_command(MyShell, 'List/search local commands', 'lsearch-command', 'lsc')
def lsc(my_shell: MyShell, pattern: str = None) -> None:
    '''Lists all commands in the local computers path, that match the regex

Examples: 
- "sc ^php" will find all commands that start with "php"
- "sc admin" will find any commands that contain the word "admin"'''
    commands = my_shell.executor.get_commands(LOCAL, pattern)
    print('\n'.join(commands))

@make_command(MyShell, 'test 123', 'test')
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

