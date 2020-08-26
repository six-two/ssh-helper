# pylint: disable=unused-wildcard-import
import cmd
import os
from typing import List, Sequence, Optional
import re
# Local modules
from .common import *
from .executor import Executor
from .ssh_utils import SshSettings
from .my_decorators import *
# External libraries. Might need no be installed via pip
import termcolor
from tabulate import tabulate


NAME = 'Dummie{}ell'.format(termcolor.colored('SSH', 'red'))
HELP_TIP = 'Type "help" or "?" to list commands.'

def print_usage_table(cls) -> None:
    commands = []
    for member_name in dir(cls):
        if member_name.startswith('command_'):
            commands.append(getattr(cls, member_name))

    descriptions = []
    descriptions.append(('?', 'Alias for "help"'))
    descriptions.append(('!', 'Alias for "shell"'))
    descriptions.append(('help', 'Shows usage for available commands'))
    for c in set(commands):
        name = c.names[0]
        descriptions.append((name, c.short_description))
        for alias_name in c.names[1:]:
            descriptions.append((alias_name, f'Alias for "{name}"'))
    descriptions = sorted(descriptions)

    table = tabulate(descriptions, headers=['Command', 'Description'], tablefmt="psql")
    print(f'\n{table}\n')

class MyShell(cmd.Cmd):
    intro = f'Welcome to the {NAME}. {HELP_TIP}\n'

    def __init__(self, ssh_settings: Optional[SshSettings]) -> None:
        super().__init__()
        self.executor = Executor(ssh_settings)
        self.prompt = '(You should not see this message)'

    def preloop(self) -> None:
        self.executor.initialize()
        self.update_prompt()

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
            dirname = os.path.basename(self.executor.remote_path)
            prompt = f'(remote: {dirname}) '
        elif self.executor.local_path:
            dirname = os.path.basename(self.executor.local_path)
            prompt = f'(local: {dirname}) '
        else:
            prompt = '(Error: no path defined) '
        self.prompt = termcolor.colored(prompt, 'blue')

    def default(self, line: str) -> bool:
        '''Executed if the user input matches no defined command'''
        command = line.split()[0]
        print(err(f'Unknown command: "{command}"'))
        print(HELP_TIP)
        return False

    def do_help(self, arg: str) -> None:
        '''Usage: (help | ?) [command]

If command is given, a help message about the command will be shown.
Otherwise a list of valid commands and their usage is displayed'''
        if not arg:
            print_usage_table(MyShell)
        else:
            # Work around for '??' and '?!'
            if arg == '?':
                arg = 'help'
            elif arg == '!':
                arg = 'shell'
            super().do_help(arg)
