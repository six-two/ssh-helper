# pylint: disable=unused-wildcard-import
import functools
import traceback
from typing import Optional, Callable, Any, List, Sequence
# Local modules
from .common import *
from .executor import CommandExecutionFailed

# TODO remove
def _parse_arguments(arg: str) -> List[str]:
    #TODO this is just a bandaid, needs support for escaped spaces / real argument parsing
    return [a for a in arg.split(' ') if a]

def make_box_message(title: str, message: str, line_length=80) -> str:
    header = f' {title} '.center(line_length, '=')
    end = '=' * line_length
    return f'\n{header}\n{message.strip()}\n{end}'


def print_exceptions(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapper_print_exceptions(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except CommandExecutionFailed as ex:
            print(err(make_box_message('Command failed', str(ex))))
        except Exception:
            print(err(make_box_message('Internal error', traceback.format_exc())))
    return wrapper_print_exceptions

# TODO remove
def arg_count(mini: int, maxi: int = None) -> Callable:
    '''
    Checks the number of arguments that a method receives.
    If called with just mini, expect len(args) == mini.
    If called with two arguments, expect mini <= len(args) <= maxi.
    If there is a mismatch of arguments, it prints the usage of the command (if available).
    '''
    def decorator_arg_count(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper_arg_count(self, arg: str):
            args = _parse_arguments(arg)
            error_arg_count = None
            max_i = maxi if maxi else mini
            
            if mini <= len(args) <= max_i:
                return fn(self, *args)
            else:
                if mini == max_i:
                    error_arg_count = 'exactly ' + pluralize(mini, 'argument')
                else:
                    error_arg_count = f'between {mini} and {max_i} arguments'

                real_arg_count = pluralize(len(args), 'argument')
                print(err(f'This command expects {error_arg_count}, but it got {real_arg_count}!'))
                print_usage(fn)

        return wrapper_arg_count
    return decorator_arg_count

def decorate_all_methods_starting_with(decorator: Callable[[Callable], Callable], pattern_list: List[str]) -> Callable:
    def wrapper_decorate_all_methods_starting_with(my_object):
        for pattern in pattern_list:
            for member_name in my_object.__dict__:
                member = getattr(my_object, member_name)
                if member_name.startswith(pattern) and callable(member):
                    # Update the method with the decorated version
                    setattr(my_object, member_name, decorator(member))
        return my_object
    return wrapper_decorate_all_methods_starting_with

# Put here to prevent a circular import error
from .command_builder import Command

def make_command(cls, name, *aliases) -> Callable:
    '''This decorator does not actually modify the function, it just adds it to the given "cls".'''
    def decorator_make_command(fn: Callable) -> Callable:
        names = [name, *aliases]
        Command(fn, names).apply_to(cls)
        return fn
    return decorator_make_command
