# pylint: disable=unused-wildcard-import
from typing import Callable
import functools
import traceback
# Local
from .common import *
from .complete import UsageException
from .executor import NoRemoteException
# External
from py_derive_cmd import Settings, CommandInfo

class MySettings(Settings):
    def handle_exceptions(self, command: 'CommandInfo', function_that_might_fail: Callable) -> Callable:
        '''
        A wrapper method (decorator) that should catch all exceptions and log / print them.
        It is used for created do_command and complete_command functions
        '''
        @functools.wraps(function_that_might_fail)
        def wrapper_print_exceptions(*args, **kwargs):
            try:
                return function_that_might_fail(*args, **kwargs)
            except UsageException as ex:
                print(err(str(ex)))
                print('Expected parameters:', command.usage_params)
            except NoRemoteException:
                print(err('No remote is defined'))
                print('Hint: Start this program with --help to see how to specify a remote host')
            except Exception:
                self.print_error(self.make_box_message('Internal error', traceback.format_exc()))
        return wrapper_print_exceptions
