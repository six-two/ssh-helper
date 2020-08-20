# pylint: disable=unused-wildcard-import
import functools
import traceback
from typing import Optional, Callable, Any, List
# Local modules
from .common import *

def _parse_arguments(arg: str) -> List[str]:
    #TODO this is just a bandaid, needs support for escaped spaces / real argument parsing
    return [a for a in arg.split(' ') if a]


def print_exceptions(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapper_print_exceptions(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            header = ' Internal error '.center(80, '=')
            error = traceback.format_exc()
            end = '=' * 80
            message = f'\n{header}\n{error}\n{end}'
            
            print(err(message))
    return wrapper_print_exceptions

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
                if fn.__doc__:
                    usage = fn.__doc__.split('\n')[0]
                    print(usage)
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