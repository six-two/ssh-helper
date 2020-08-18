# pylint: disable=unused-wildcard-import
import functools
import traceback
from typing import Optional, Callable, Any, List
# Local modules
from common import *


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

def no_args(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapper_no_args(self, arg: str):
        if arg:
            fn_name = fn.__name__[3:]  # remove the leading "do_"
            print(err('This command expects no arguments!'))
            print(f'Hint: Try just running "{fn_name}" with nothing after it')
        else:
            return fn(self, arg)
    return wrapper_no_args

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