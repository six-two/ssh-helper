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
from .complete import UsageException


class Command:
    def __init__(self, fn: Callable, names: Sequence[str]) -> None:
        if len(names) < 1:
            raise Exception('Trying to create command with no name(s)')

        self.fn = fn
        self.names = names
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

    def apply_to(self, cls) -> None:
        complete_command = self.create_complete_command()

        for name in self.names:
            if getattr(cls, f'do_{name}', None) is not None:
                raise Exception(f'Duplicate definition of method "do_{name}"')
            setattr(cls, f'do_{name}', self.create_do_command(name))
            if len(self.params) != 0:
                setattr(cls, f'complete_{name}', complete_command)
            setattr(cls, f'help_{name}', self.help_command)

    def parse_args(self, args: Sequence[str]) -> Optional[List]:
        parsed = []
        print_debug(f'before parse: {args}')
        for i in range(len(args)):
            # Get the class of the parameter
            param_cls = self.params[i].annotation
            arg: Any = args[i]

            if param_cls != inspect.Parameter.empty:
                try:
                    # Replace the argument with its parsed value
                    arg = param_cls(arg)
                except UsageException as ex:
                    # Print an error message and
                    print(err(f'Usage error in argument {i+1}: {ex}'))
                    return None
                print_debug(f'Param converted to {param_cls}')
            else:
                print_debug('Param {i}: No type in method signature')

            parsed.append(arg)

        print_debug(f'after parse: {parsed}')
        return parsed

    def create_do_command(self, name: str) -> Callable:
        def wrapper_do_command(self_of_cmd, args_str: str) -> bool:
            args = split_args(args_str)

            if self.min_args <= len(args) <= self.max_args:
                parsed_args = self.parse_args(args)
                if parsed_args is not None:
                    ret = self.fn(self_of_cmd, *parsed_args)
                    return bool(ret)
                else:
                    print_debug('Usage error')
                    return False
            else:
                real_arg_count = pluralize(len(args), 'argument')
                print(err(self.err_arg_count.format(real_arg_count)))
                print(f'Usage: {name} {self.usage_params}')
                return False

        return print_exceptions(wrapper_do_command)

    def help_command(self):
        print(f'Usage: {self.names[0]} {self.usage_params}')
        if len(self.names) > 1:
            alias_str = ', '.join(self.names[1:])
            print(f'Aliases: {alias_str}')
        if self.fn.__doc__:
            print('\n' + self.fn.__doc__)

    def create_complete_command(self):
        @print_exceptions
        def wrapper_complete_command(self_of_cmd, text: str, line: str, begidx: int, endidx: int) -> List[str]:
            # Cut it off at the cursor
            before_cursor = line[:endidx]
            # Remove the command name
            before_cursor = before_cursor.split(' ', maxsplit=1)[1]

            print_debug(before_cursor)
            args = split_incomplete_args(before_cursor)
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

def split_incomplete_args(incomplete_arg_str: str) -> List[str]:
    # add character to test if the last param should be extended
    # or if a new argument should be started
    TEST_STRING = '_new'
    before_cursor = incomplete_arg_str + TEST_STRING
    args = split_args(before_cursor, may_be_cut_off=True)
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


def split_args(arg_str: str, may_be_cut_off=False) -> List[str]:
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
