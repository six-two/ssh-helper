# pylint: disable=unused-wildcard-import
import os
import re
from typing import List, Optional, Callable
# Local
from . import *


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

@make_command(settings, 'Open a remote shell', aliases=['r'], raw_arg=True)
def shell(my_shell: MyShell, arg: str) -> None:
    '''If called without arguments, it will open a new interactive ssh session with the remote computer.
If called with a unix_command, it will run the unix_command on the remote machine.
You can also use "!" as an alias for this command.

Example:
- "shell" will open a remote interactive shell
- "!uname -a" will run "uname -a" on the remote computer'''
    my_shell.executor.shell(REMOTE, arg)

@make_command(settings, 'Open a local shell', aliases=['l'], raw_arg=True)
def lshell(my_shell: MyShell, arg: str) -> None:
    '''If called without arguments, it will open a new interactive shell on the local computer.
If called with arguments, it will run the arguments in a shell on the local machine'''
    my_shell.executor.shell(LOCAL, arg)

@make_command(settings, 'Exit this shell', aliases=['quit', 'EOF'])
def exit(my_shell: MyShell) -> bool:
    '''Exit this interactive shell.
You can trigger this by pressing Ctrl-D on an empty prompt.'''
    return True

@make_command(settings, 'Delete a remote file')
def rm(my_shell: MyShell, path: RFile) -> None:
    '''Remove the file with the given path from the remote computer'''
    my_shell.executor.execute(REMOTE, ['rm', path.value()])

@make_command(settings, 'Delete a local file')
def lrm(my_shell: MyShell, path: LFile) -> None:
    '''Remove the file with the given path from the local computer'''
    my_shell.executor.execute(LOCAL, ['rm', path.value()])

@make_command(settings, 'Delete a remote folder')
def rmdir(my_shell: MyShell, path: RFolder) -> None:
    '''Remove the directory with the given path from the remote computer'''
    my_shell.executor.execute(REMOTE, ['rm', '-r', path.value()])

@make_command(settings, 'Delete a local folder')
def lrmdir(my_shell: MyShell, path: LFolder) -> None:
    '''Remove the directory with the given path from the local computer'''
    my_shell.executor.execute(LOCAL, ['rm', '-r', path.value()])

@make_command(settings, 'Edit a remote file', aliases=['e'])
def edit(my_shell: MyShell, path: RFile) -> None:
    '''Edit the file located at path on the remote computer'''
    my_shell.executor.execute(REMOTE, ['nano', path.value()])

@make_command(settings, 'Edit a local file', aliases=['le'])
def ledit(my_shell: MyShell, path: LFile) -> None:
    '''Edit the file located at path on the remote computer'''
    my_shell.executor.execute(LOCAL, ['nano', path.value()])

@make_command(settings, 'View a remote file', aliases=['v'])
def view(my_shell: MyShell, path: RFile) -> None:
    '''View the file located at path on the remote computer'''
    # TODO automatic detection of available commands: less, more, cat
    my_shell.executor.execute(REMOTE, ['less', path.value()])

@make_command(settings, 'View a local file', aliases=['lv'])
def lview(my_shell: MyShell, path: LFile) -> None:
    '''View the file located at path on the local computer'''
    # TODO automatic detection of available commands: less, more, cat
    my_shell.executor.execute(LOCAL, ['less', path.value()])

@make_command(settings, 'List/search remote commands', aliases=['sc'])
def search_commands(my_shell: MyShell, pattern: str = None) -> None:
    '''Lists all commands in the remote computers path, that match the regex.

Examples:
- "sc ^php" will find all commands that start with "php"
- "sc admin" will find any commands that contain the word "admin"'''
    commands = my_shell.executor.all_commands(REMOTE)
    print_matching(commands, pattern)

@make_command(settings, 'List/search local commands', aliases=['lsc'])
def lsearch_commands(my_shell: MyShell, pattern: str = None) -> None:
    '''Lists all commands in the local computers path, that match the regex

Examples:
- "sc ^php" will find all commands that start with "php"
- "sc admin" will find any commands that contain the word "admin"'''
    commands = my_shell.executor.all_commands(REMOTE)
    print_matching(commands, pattern)

@make_command(settings, 'Execute a remote file')
def run(my_shell: MyShell, path: RFile) -> None:
    '''Mark the given file as executeable and then execute it'''
    lpath = os.path.join('.', path.value())
    chmod_and_exec = ['chmod', '+x', lpath, ';', lpath]
    my_shell.executor.execute(REMOTE, chmod_and_exec, shell=True)

@make_command(settings, 'Print remote variables', aliases=['sv'])
def search_vars(my_shell: MyShell, regex: str = None) -> None:
    '''Without arguments: Prints all remote variables.
With argument: Only variables that contain pattern'''
    env_vars = my_shell.executor.execute_in_background(REMOTE, ['printenv']).split('\n')
    print_matching(env_vars, regex, lambda l: l.split('=')[0])

@make_command(settings, 'Print local variables', aliases=['lsv'])
def lsearch_vars(my_shell: MyShell, regex: str = None) -> None:
    '''Without arguments: Prints all local variables.
With argument: Only variables that contain pattern'''
    env_vars = my_shell.executor.execute_in_background(LOCAL, ['printenv']).split('\n')
    print_matching(env_vars, regex, lambda l: l.split('=')[0])
