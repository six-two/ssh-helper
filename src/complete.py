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
from .my_shell import MyShell

class GenericFilePath(str):
    remote: Optional[IsRemote] = None
    allow_files: Optional[bool] = None

    @classmethod
    def complete(cls, my_shell: MyShell, argument_up_to_cursor: str, text: str):
        if cls.remote is None or cls.allow_files is None:
            print(f'Warning: class "{cls.__name__}" has not overwritten all required fields of GenericFilePath')
            return []
        else:
            return my_shell.executor.complete_path(cls.remote, cls.allow_files, argument_up_to_cursor, text)

    @classmethod
    def test(cls):
        print(cls.remote, cls.allow_files)

class LFile(GenericFilePath):
    remote = LOCAL
    allow_files = True

class LFolder(GenericFilePath):
    remote = LOCAL
    allow_files = False

class RFile(GenericFilePath):
    remote = REMOTE
    allow_files = True

class RFolder(GenericFilePath):
    remote = REMOTE
    allow_files = False

class SubLFile(LFile):
    pass
