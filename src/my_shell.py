# pylint: disable=unused-wildcard-import
import cmd
import os
from typing import List, Sequence, Optional
import re
# Local modules
from .common import *
from .executor import Executor
from .ssh_utils import SshSettings
# External libraries. Might need no be installed via pip
import termcolor
from tabulate import tabulate


NAME = 'Dummie{}ell'.format(termcolor.colored('SSH', 'red'))
HELP_TIP = 'Type "help" or "?" to list commands.'

def print_usage_table(cls) -> None:
    info_map = {}
    for command in get_settings().registered_commands:
        name = command.names[0]
        aliases = command.names[1:]
        info_map[name] = (aliases, command.short_description)

    info_map['help'] = (['?'], 'Shows help about commands')
    info_map['shell'][0].append('!')

    descriptions = []
    descriptions.append(('Command', 'Alias(es)', 'Description'))
    for name, aliases_description in sorted(info_map.items()):
        aliases, description = aliases_description
        alias_str = ', '.join(aliases)
        descriptions.append((name, alias_str, description))

    table = tabulate(descriptions, headers='firstrow', tablefmt="psql")
    print(f'\n{table}\n')

def _rewrite_command(line: str, source_command_start: str, target_command: str, do_not_rewrite_list: Sequence[str] = []) -> str:
    command = line.split()[0]
    do_not_rewrite_list = [target_command, *do_not_rewrite_list]

    if command.startswith(source_command_start):
        command_end = command[len(source_command_start):]
        if command_end and command not in do_not_rewrite_list:
            # Make everything following base the first parameter
            rewritten_command = f'{target_command} {command_end}'
            new_line = line.replace(command, rewritten_command, 1)
            print_debug(f'Rewritten "{line}" to "{new_line}"')
            return new_line
    return line

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
        line = _rewrite_command(line, 'ls', 'ls_format')
        line = _rewrite_command(line, 'lls', 'lls_format')
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
