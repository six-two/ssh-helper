#!/usr/bin/env python3
# pylint: disable=unused-wildcard-import
from typing import Callable, Sequence, Tuple, Optional, List, Any
from enum import Enum, auto
import collections
import inspect
#local
# from .common import *
# from .executor import Executor
LOCAL = False
REMOTE = True
Executor = Any

class GenericFilePath(str):
    remote: Optional[bool] = None
    allow_files: Optional[bool] = None

    @classmethod
    def complete(cls, executor: Executor, argument_up_to_cursor, text):
        if cls.remote is None or cls.allow_files is None:
            print(f'Warning: class "{cls.__name__}" has not overwritten all required fields of GenericFilePath')
            return []
        else:
            return executor.complete_path(cls.remote, cls.allow_files, argument_up_to_cursor, text)

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


# IDEA: use anotations for completion info

def get_complete_info(fn: Callable) -> List:
    params = get_non_self_parameters(fn)
    annotations = [p.annotation for p in params]
    for a in annotations:
        try:
            print(a.__name__)
            a.test()
        except Exception as e:
            print(e)
    print(annotations)
    return annotations

def get_non_self_parameters(fn: Callable) -> List[inspect.Parameter]:
    s = inspect.signature(fn)
    params = list(s.parameters.values())
    if len(params) >= 1 and params[0].name == 'self':
        params = params[1:]
    return params

def param_to_help_text(p: inspect.Parameter) -> str:
    name = p.name
    name = name.upper()
    optional = p.default != inspect.Parameter.empty
    return f'[{name}]' if optional else f'<{name}>'

def generate_usage_string(fn: Callable) -> str:
    name = fn.__name__
    params = [param_to_help_text(p) for p in get_non_self_parameters(fn)]
    params_str = ' '.join(params)
    return f'{name} {params_str}'
        

if __name__ == '__main__':
    def test(a: str, b: RFolder, c: LFile=None):
        pass
    print(generate_usage_string(test))
    print(get_complete_info(test))
    RFolder('abc').test()
