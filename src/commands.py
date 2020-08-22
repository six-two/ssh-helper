# pylint: disable=unused-wildcard-import
from .my_shell import MyShell
from .command_builder import *
from .complete import *
from .my_decorators import make_command

@make_command(MyShell, 'tls', 'atls', 'btls')
def tls(my_shell: MyShell, path: RFile = None, lpath: LFile = None):
    print('path:', path)
    print('lpath:', lpath)
