# pylint: disable=unused-wildcard-import
from .common import *
from .my_shell import MyShell
from .command_builder import *
from .complete import *
from .my_decorators import make_command

@make_command(MyShell, 'tls', 'atls', 'btls')
def tls(my_shell: MyShell, path: RFile = None, lpath: LFile = None) -> None:
    'test 123'
    print('path:', path)
    print('lpath:', lpath)

@make_command(MyShell, 'debug')
def debug(my_shell: MyShell, enable: BoolOption) -> None:
    '''Enables / disables debugging output. This may interfere with some features like command completion'''
    set_debug(enable.value())
    print(f'Debug enabled: {enable.value()}')
