# Prevent the includes from being imported when common is imported with a wildcard (*) import
import typing as _typing
# External libraries. Might need no be installed via pip
import termcolor as _termcolor

IsRemote = _typing.NewType('IsRemote', bool)
REMOTE = IsRemote(True)
LOCAL = IsRemote(False)

_DEBUG = False
USAGE = 'Usage: '

def print_usage(method: _typing.Callable) -> None:
    usage = get_usage(method)
    if usage:
        print(USAGE + usage)
    else:
        print('Usage description not available')

def get_usage(method: _typing.Callable) -> _typing.Optional[str]:
    if method.__doc__:
        usage = method.__doc__.split('\n')[0]
        if usage.startswith(USAGE):
            return usage[len(USAGE):]
        else:
            print(warn(f'[Warning] Bad usage format in method "{method.__name__}"'))
    else:
        print(warn(f'[Warning] No docstring for method "{method.__name__}"'))
    return None

def pluralize(count: int, word: str) -> str:
    plural = '' if count == 1 else 's'
    return f'{count} {word}{plural}'

def err(message: str):
    '''Creates a colored string to be printed. It uses the standard error color'''
    return _termcolor.colored(message, "red")

def warn(message: str):
    '''Creates a colored string to be printed. It uses the standard warning color'''
    return _termcolor.colored(message, "yellow")

def is_debug() -> bool:
    return _DEBUG

def print_debug(msg: _typing.Any) -> None:
    if _DEBUG:
        print(msg)

def set_debug(new_value: bool) -> None:
    global _DEBUG
    _DEBUG = new_value
