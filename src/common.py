# Prevent the includes from being imported when common is imported with a wildcard (*) import
import typing as _typing
# External libraries. Might need no be installed via pip
import termcolor as _termcolor
from py_derive_cmd import make_command, Settings


IsRemote = _typing.NewType('IsRemote', bool)
REMOTE = IsRemote(True)
LOCAL = IsRemote(False)

_DEBUG = False
_settings: _typing.Optional[Settings] = None

def get_settings() -> Settings:
    global _settings

    if _settings is None:
        from .my_shell import MyShell
        from .settings_overwrite import MySettings
        _settings = MySettings(MyShell)

    return _settings

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
