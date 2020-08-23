#!/usr/bin/env python3
# pylint: disable=unused-wildcard-import
from typing import Callable, Sequence, Tuple, Optional, List, Any
from enum import Enum, auto
import collections
import inspect
import shlex
import functools
#local
from .common import *


class UsageException(Exception):
    pass


class GenericOption:
    def __init__(self, arg_str) -> None:
        '''Parse the value. It may throw an exception, if the argument is malformatted / invalid'''
        self.raw = arg_str

    def value(self) -> Any:
        return self.raw

    @classmethod
    def complete(cls, my_shell, argument_up_to_cursor: str, text: str) -> List[str]:
        return []

    @classmethod
    def describe(cls) -> str:
        return 'No description available'

def option_list_to_string(options: List[str]) -> str:
    if len(options) < 2:
        raise Exception('Has to has at least two options')
    joined = '", "'.join(options)
    return f'"{joined}"'

class OptionList(GenericOption):
    options: List[str] = []

    def __init__(self, arg_value):
        super().__init__(arg_value)
        if arg_value not in self.options:
            raise UsageException(f'Invalid option: got "{arg_value}", but expected one of {option_list_to_string(self.options)}')

    @classmethod
    def complete(cls, my_shell, argument_up_to_cursor: str, text: str) -> List[str]:
        return [o for o in cls.options if o.startswith(text)]

    @classmethod
    def describe(cls) -> str:
        return 'Valid values: ' + option_list_to_string(cls.options)

    @classmethod
    def parse(cls, arg: str) -> str:
        '''Parse the value. It may throw an UsageException, if the argument is malformatted / invalid'''
        if arg not in cls.options:
            raise UsageException(f'Invalid option: got "{arg}", but expected one of {option_list_to_string(cls.options)}')
        else:
            return arg        

class BoolOption(OptionList):
    options = ['true', 'false']

    def value(self) -> bool:
        return self.raw == 'true'

class GenericFilePath(GenericOption):
    remote: Optional[IsRemote] = None
    allow_files: Optional[bool] = None

    @classmethod
    def complete(cls, my_shell, argument_up_to_cursor: str, text: str) -> List[str]:
        if cls.remote is None or cls.allow_files is None:
            print(f'Warning: class "{cls.__name__}" has not overwritten all required fields of GenericFilePath')
            return []
        else:
            return my_shell.executor.complete_path(cls.remote, cls.allow_files, argument_up_to_cursor, text)


class LFile(GenericFilePath):
    remote = LOCAL
    allow_files = True
    
    @classmethod
    def describe(cls) -> str:
        return 'The path of a local file (sometimes folders are valid too)'

class LFolder(GenericFilePath):
    remote = LOCAL
    allow_files = False

    @classmethod
    def describe(cls) -> str:
        return 'The path of a local folder'

class RFile(GenericFilePath):
    remote = REMOTE
    allow_files = True

    @classmethod
    def describe(cls) -> str:
        return 'The path of a remote file (sometimes folders are valid too)'

class RFolder(GenericFilePath):
    remote = REMOTE
    allow_files = False

    @classmethod
    def describe(cls) -> str:
        return 'The path of a remote folder'
