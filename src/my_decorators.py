# pylint: disable=unused-wildcard-import
import functools
import traceback
from typing import Optional, Callable, Any, List, Sequence
# Local modules
from .common import *
from .executor import CommandExecutionFailed, NoRemoteException

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
        except NoRemoteException:
            print(err('You have not configured a remote server!'))
        except Exception:
            print(err(make_box_message('Internal error', traceback.format_exc())))
    return wrapper_print_exceptions

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

def make_command(cls, short_description: str, name: str, *aliases: str, raw_arg: bool = False) -> Callable:
    '''This decorator does not actually modify the function, it just adds it to the given "cls".'''
    def decorator_make_command(fn: Callable) -> Callable:
        names = [name, *aliases]
        Command(fn, names, short_description, raw_arg=raw_arg).apply_to(cls)
        return fn
    return decorator_make_command
