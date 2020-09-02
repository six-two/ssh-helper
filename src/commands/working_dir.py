from . import *

@make_command(settings, 'Print current working directories')
def pwd(my_shell: MyShell) -> None:
    '''Show the full path of your current working directories'''
    # Remove trailing \n
    lpwd = my_shell.executor.execute_in_background(LOCAL, ['pwd'])[:-1]
    print(f'Local working directory:  "{lpwd}"')

    try:
        rpwd = my_shell.executor.execute_in_background(REMOTE, ['pwd'])[:-1]
        print(f'Remote working directory: "{rpwd}"')
    except NoRemoteException:
        print('Remote working directory:', warn('<Remote is disabled>'))

@make_command(settings, 'Change remote working directory')
def cd(my_shell: MyShell, path: RFolder = RFolder('')) -> None:
    '''If a path is given, the remote working directory is set to path.
If no path is given, the remote working directory is set to the users home directory.'''
    my_shell.executor.cd(REMOTE, path.value())

@make_command(settings, 'Change local working directory')
def lcd(my_shell: MyShell, path: LFolder = LFolder('')) -> None:
    '''If a path is given, the local working directory is set to path.
If no path is given, the local working directory is set to the users home directory.'''
    my_shell.executor.cd(LOCAL, path.value())

