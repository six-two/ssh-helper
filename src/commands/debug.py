from . import *

@make_command(settings, 'Debug: Prints methods')
def show_methods(my_shell: MyShell) -> None:
    '''Prints all methods defined on the shell object'''
    print_debug('Debug is enabled\n')
    import inspect
    for member_name in sorted(dir(my_shell)):
        member = getattr(my_shell, member_name)
        if callable(member) and not member_name.startswith('__'):
            print(member_name, end='')
            try:
                print(inspect.signature(member))
            except:
                print(' <-- Could not determine signature')

@make_command(settings, 'Echos the path to a remote file')
def echo_rfile(my_shell: MyShell, path: RFile):
    print(f'Path: "{path.value()}"')

@make_command(settings, 'Enable/disable debugging')
def debug(my_shell: MyShell, enable: BoolOption) -> None:
    '''Enables / disables debugging output. This may interfere with some features like command completion'''
    set_debug(enable.value())
    print(f'Debug enabled: {enable.value()}')

@make_command(settings, 'Cause an error')
def error(my_shell: MyShell) -> None:
    '''Causes an internal error. Used to test exception handling'''
    raise Exception('Test exception')
