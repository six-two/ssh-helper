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
from .arguments import param_to_help_text, arg_counts, split_args, split_incomplete_args, parse_args


class Command:
    def __init__(self, fn: Callable, names: Sequence[str], short_description: str, raw_arg: bool = False) -> None:
        if len(names) < 1:
            raise Exception('Trying to create command with no name(s)')

        self.fn = fn
        self.names = names
        self.short_description = short_description
        self.use_raw_arg = raw_arg
        # Remove the self / my_shell / cmd parameter
        self.params = list(inspect.signature(fn).parameters.values())[1:]
        self.usage_params = ' '.join([param_to_help_text(p) for p in self.params])
        self.min_args, self.max_args = arg_counts(self.params)

        if not fn.__doc__:
            print(warn(f'Method {fn.__name__} has no doc string'))
            fn.__doc__ = 'No description is available for this command'

        if self.min_args == self.max_args:
            error_arg_count = 'exactly ' + pluralize(self.min_args, 'argument')
        else:
            error_arg_count = f'between {self.min_args} and {self.max_args} arguments'
        self.err_arg_count = f'This command expects {error_arg_count}, but it got {{}}!'

    def apply_to(self, cls) -> None:
        complete_command = self.create_complete_command()
        help_command = print_exceptions(self.help_command)

        for name in self.names:
            if getattr(cls, f'do_{name}', None) is not None:
                raise Exception(f'Duplicate definition of method "do_{name}"')

            # Register the do_method, that performs the action
            setattr(cls, f'do_{name}', self.create_do_command(name))

            if len(self.params) != 0:
                # Add a method that handels tab-completion of the arguments
                setattr(cls, f'complete_{name}', complete_command)

            # Add a method that handels "?command" / "help command"
            setattr(cls, f'help_{name}', help_command)

            # Add a (non_standard) method that can be used to get infos about this command
            setattr(cls, f'command_{name}', self)

    def create_do_command(self, name: str) -> Callable:
        def wrapper_do_command(self_of_cmd, args_str: str) -> bool:
            if self.use_raw_arg:
                return bool(self.fn(self_of_cmd, args_str))
            else:
                args = split_args(args_str)

                if self.min_args <= len(args) <= self.max_args:
                    parsed_args = parse_args(self.params, args)
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

    def help_command(self, self_of_cmd):
        print(f'Usage: {self.names[0]} {self.usage_params}')
        if len(self.names) > 1:
            alias_str = ', '.join(self.names[1:])
            print(f'Aliases: {alias_str}')
        if self.fn.__doc__:
            print('\n' + self.fn.__doc__)

    def create_complete_command(self):
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
        return print_exceptions(wrapper_complete_command)
