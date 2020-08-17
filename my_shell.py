import cmd
import os
# Local modules
from common import *
from executor import Executor
from my_decorators import *

NAME = 'Dummie{}ell'.format(termcolor.colored('SSH', 'red'))
HELP_TIP = 'Type "help" or "?" to list commands.'
USAGE = """
ssh-helper

Some commands can be executed on either localy or remotely. They are prefixed with a "(l)" like in "(l)pwd".
In this case use "pwd" to execute the command on the remote machine, use "lpwd" to execute the command on the local machine
Other conventions: 
  <mandatory_argument>
  [optional_argument]
  (use_either_this_command | or_use_this_one)

Commands:
d                | Enable debug mode
(l)pwd           | Print the working directory's path
(l)ls [path]     | Lists all files and directories in the working directory (or path if supplied)
(l)cd [path]     | Change the working directory (to path if supplied, otherwise to the users home directory)
(help | ?)       | Show this help message
(help | ?) <cmd> | Shows help about the given command
(shell | !)      | Opens an interactive ssh session. Exit it as usual (via "exit" or Ctrl-D)
(shell | !) <cmd>| The given command will be run in a shell on the remote machine
"""


@decorate_all_methods_starting_with(print_exceptions, ['do_', 'complete_', 'help_'])
class MyShell(cmd.Cmd):
    intro = f'Welcome to the {NAME}. {HELP_TIP}\n'

    def __init__(self, ssh_helper):
        super().__init__()
        self.executor = Executor(ssh_helper)
        self.prompt = '(You should not see this message)'

        # def signal_handler(sig, frame):
        #     print('You pressed Ctrl+C!')
            
        # signal.signal(signal.SIGINT, signal_handler)


    def preloop(self):
        self.executor.initialize()
        self.update_prompt()

    def complete_path_single_argument(self, remote, allow_files, text, line, begidx, endidx):
        line_before_cursor = line[:endidx]
        command, argument_before_cursor = line_before_cursor.split(' ', 1)
        print_debug(f'Single arg complete for "{command}"')
        return self.complete_path(remote, allow_files, argument_before_cursor, text)

    def postcmd(self, stop, line):
        '''Update the prompt after running a command'''
        self.update_prompt()
        return stop

    def update_prompt(self):
        remote_dirname = os.path.basename(self.executor.remote_path)
        prompt = f'({remote_dirname}) '
        self.prompt = termcolor.colored(prompt, 'blue')

    def default(self, line):
        '''Executed if the user input matches no defined command'''
        command = line.split()[0]
        print(err(f'Unknown command: "{command}"'))
        print(HELP_TIP)

    @no_args
    def do_EOF(self, arg):
        '''Usage: EOF
Exit this shell. You can also trigger this by pressing Ctrl-D on an empty prompt'''
        return True

    @no_args
    def do_exit(self, arg):
        '''Usage: exit
Exit this interactive shell'''
        return True

    def do_shell(self, arg):
        '''Usage: (shell | !) [unix_command]
If called without arguments, it will open a new interactive ssh session.
If called with a unix_command, it will run the unix_command on the remote machine'''
        # print(f'Got command: "{arg}"')
        self.executor.shell(arg)

    def do_help(self, arg):
        '''Usage: help [command]
If command is given, a help message about the command will be shown.
Otherwise a list of valid commands and their usage is displayed'''
        if not arg:
            print(USAGE)
        else:
            super().do_help(arg)

    @no_args
    def do_d(self, arg):
        set_debug(True)
        print("Debug mode enabled!")

    @no_args
    def do_error(self, arg):
        raise Exception('Test exception')

# ======================= (l)ls =======================
    def do_ls(self, arg):
        '''Usage: ls [path]
List the files in the current directory or in the given path on the remote computer'''
        self.executor.ls(arg, remote=True)

    def complete_ls(self, *args):
        return self.complete_path_single_argument(True, True, *args)

    def do_lls(self, arg):
        '''Usage: lls [path]
List the files in the current directory or in the given path on the local computer'''
        self.executor.ls(arg, remote=False)

    def complete_lls(self, *args):
        return self.complete_path_single_argument(False, True, *args)

# ======================= (l)pwd =======================

    @no_args
    def do_pwd(self, arg):
        '''Usage: pwd
Show the full path of your current working directory on the remote computer'''
        self.executor.pwd(remote=True)

    @no_args
    def do_lpwd(self, arg):
        '''Usage: lpwd
Show the full path of your current working directory on the local computer'''
        self.executor.pwd(remote=False)

# ======================= (l)cd =======================
    def do_cd(self, arg):
        '''Usage: cd [path]
If a path is given, the remote working directory is set to path.
If no path is given, the remote working directory is set to the users home directory.'''
        self.executor.cd(arg, remote=True)

    def complete_cd(self, *args):
        return self.complete_path_single_argument(True, False, *args)

    def do_lcd(self, arg):
        '''Usage: cd [path]
If a path is given, the local working directory is set to path.
If no path is given, the local working directory is set to the users home directory.'''
        self.executor.cd(arg, remote=False)

    def complete_lcd(self, *args):
        return self.complete_path_single_argument(False, False, *args)
