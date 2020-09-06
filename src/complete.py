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
from .executor import CommandExecutionFailed, NoRemoteException
# Libraries
from py_derive_cmd import GenericOption, complete_path


def list_files_factory(my_shell, remote: IsRemote, allow_files: bool) -> Callable:
    def list_files_result(folder: str) -> List[str]:
        ls_command = ['ls', '-1', '--escape', '--indicator-style=slash', '-A', '--color=never', folder]
        output = my_shell.executor.execute_in_background(remote, ls_command)
        file_names = output.split('\n')
        if not allow_files:
            file_names = [f for f in file_names if f.endswith('/')]
        return file_names

    return list_files_result


class GenericFilePath(GenericOption):
    remote: Optional[IsRemote] = None
    allow_files: Optional[bool] = None

    @classmethod
    def complete(cls, my_shell, argument_up_to_cursor: str, text: str) -> List[str]:
        if cls.remote is None or cls.allow_files is None:
            print(f'Warning: class "{cls.__name__}" has not overwritten all required fields of GenericFilePath')
        else:
            try:
                fn_list_files = list_files_factory(my_shell, cls.remote, cls.allow_files)
                return complete_path('.', fn_list_files, argument_up_to_cursor, text)
            except CommandExecutionFailed as ex:
                print_debug(ex)
            except NoRemoteException:
                pass
            except Exception as ex:
                # TODO log these in a file somewhere?
                print(err(str(ex)))

        return []

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
