#!/usr/bin/env python3
# pylint: disable=unused-wildcard-import
from typing import Callable, Sequence, Tuple, Optional, List, Any
from enum import Enum, auto
import collections
import inspect
import shlex
import functools
import traceback
#local
from .common import *
from .my_decorators import print_exceptions


class Command:
    def __init__(self, fn: Callable) -> None:
        self.fn = fn
        if not fn.__doc__:
            print(warn(f'Method {fn.__name__} has no doc string'))
            fn.__doc__ = 'No description is available for this command'
        # Remove the self / my_shell / cmd parameter
        self.params = list(inspect.signature(fn).parameters.values())[1:]
        self.usage_params = ' '.join([param_to_help_text(p) for p in self.params])
        self.min_args, self.max_args = arg_counts(self.params)

        if self.min_args == self.max_args:
            error_arg_count = 'exactly ' + pluralize(self.min_args, 'argument')
        else:
            error_arg_count = f'between {self.min_args} and {self.max_args} arguments'
        self.err_arg_count = f'This command expects {error_arg_count}, but it got {{}}!'

    def apply_to(self, cls, names: Sequence[str]) -> None:
        if len(names) < 1:
            raise Exception('Trying to create command with no name(s)')

        help_header = f'Usage: {names[0]} {self.usage_params}'
        if len(names) > 1:
            alias_str = ', '.join(names[1:])
            help_header += f'\nAliases: {alias_str}'

        self.fn.__doc__ = f'{help_header}\n\n{self.fn.__doc__}'
        complete_command = self.create_complete_command()

        for name in names:
            if getattr(cls, f'do_{name}', None) is not None:
                raise Exception(f'Duplicate definition of method "do_{name}"')
            setattr(cls, f'do_{name}', self.create_do_command(name))
            setattr(cls, f'complete_{name}', complete_command)

    def create_do_command(self, name: str) -> Callable:
        @functools.wraps(self.fn)
        @print_exceptions
        def wrapper_do_command(self_of_cmd, args_str: str):
            args = parse_args(args_str)

            if self.min_args <= len(args) <= self.max_args:
                return self.fn(self_of_cmd, *args)
            else:
                real_arg_count = pluralize(len(args), 'argument')
                print(err(self.err_arg_count.format(real_arg_count)))
                print(f'Usage: {name} {self.usage_params}')

        return wrapper_do_command

    def create_complete_command(self):
        @print_exceptions
        def wrapper_complete_command(self_of_cmd, text: str, line: str, begidx: int, endidx: int) -> List[str]:
            # Cut it off at the cursor
            before_cursor = line[:endidx]
            # Remove the command name
            before_cursor = before_cursor.split(' ', maxsplit=1)[1]

            print_debug(before_cursor)
            args = parse_incomplete_args(before_cursor)
            print_debug(args)

            if len(args) > self.max_args:
                print_debug('Too many args!')
                # There are already too many arguments
                return []
            
            arg_index = len(args) - 1
            last_arg = args[arg_index]
            try:
                # Get the class of the parameter
                param_cls = self.params[arg_index].annotation
                # Call the complete function, if it is defineed
                return param_cls.complete(self_of_cmd, last_arg, text)
            except:
                traceback.print_exc()
                # Complete function is probably not defined
                return []
        return wrapper_complete_command

def parse_incomplete_args(incomplete_arg_str: str) -> List[str]:
    # add character to test if the last param should be extended
    # or if a new argument should be started
    TEST_STRING = '_new'
    before_cursor = incomplete_arg_str + TEST_STRING
    args = parse_args(before_cursor, may_be_cut_off=True)
    # Remove TEST_STRING
    if args[-1] == TEST_STRING:
        # Keep the empty argument to complete
        args[-1] = ''
    elif args[-1].endswith(TEST_STRING):
        args[-1] = args[-1][:-len(TEST_STRING)]
    else:
        print('BUG: Argument parsing: WTF happened to the underscore?')

    print_debug(args)
    return args


def parse_args(arg_str: str, may_be_cut_off=False) -> List[str]:
    if arg_str:
        return shlex.split(arg_str)
    else:
        return []

def param_to_help_text(p: inspect.Parameter) -> str:
    name = p.name
    name = name.upper()
    optional = p.default != inspect.Parameter.empty
    return f'[{name}]' if optional else f'<{name}>'

def arg_counts(params: Sequence[inspect.Parameter]) -> Tuple[int, int]:
    max_args = len(params)
    min_args = 0
    for p in params:
        # Count how many arguments are required
        if p.default != inspect.Parameter.empty:
            break
        min_args += 1
    return (min_args, max_args)