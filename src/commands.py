# pylint: disable=unused-wildcard-import
from .common import *
from .my_shell import MyShell
from .command_builder import *
from .complete import *
from .my_decorators import make_command


@make_command(MyShell, 'debug')
def debug(my_shell: MyShell, enable: BoolOption) -> None:
    '''Enables / disables debugging output. This may interfere with some features like command completion'''
    set_debug(enable.value())
    print(f'Debug enabled: {enable.value()}')

@make_command(MyShell, 'error')
def error(self) -> None:
    '''Causes an internal error. Used to test exception handling'''
    raise Exception('Test exception')

@make_command(MyShell, 'exit', 'quit', 'EOF')
def exit(self) -> bool:
    '''Exit this interactive shell.
You can trigger this by pressing Ctrl-D on an empty prompt.'''
    return True
