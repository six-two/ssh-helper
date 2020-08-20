#!/usr/bin/env python3

'''
TODO:
add typing annotations
mv, edit, view
list_commands (all in path)
get_env
sysinfo
(upload|download)_dir
file name argument parsing
creating shortcuts (like R1, L4)
argument count macro
'''

'''
=============== Command reminder ===============
Run: /c/ssh-helper/main.py vagrant@172.28.128.3 -p vagrant
Run typechecker: mypy /c/ssh-helper/
'''

import os
import sys
import argparse
# Change current dir to enable loading the other files
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.append(src_dir)
# Import local package
# pylint: disable=import-error,no-name-in-module
from src import SshSettings, MyShell, get_available_commands, err

available_commands = ''.join([f'\n  {c}' for c in get_available_commands()])

parser = argparse.ArgumentParser(
    description='A SSH helper that is inspired by the Metasploit Meterpreter',
    epilog=f'available commands:' + available_commands,
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('user_at_host', help='<SSH username>@<hostname/IP address>')
parser.add_argument('--password', '-p', help='SSH login password')
parser.add_argument('--command', '-c', nargs='+', help='run command and exit')
args = parser.parse_args()

try:
    user, host = args.user_at_host.split('@')
except:
    print(err(f'Invalid format: "{args.user_at_host}"'))
    print('Expected format: "<SSH username>@<hostname/IP address>"')
    print('Examples: "admin@ssh.six-two.dev", "vagrant@172.28.128.3"')
    sys.exit(1)

ssh_settings = SshSettings(host, user, args.password)
shell = MyShell(ssh_settings)

try:
    if args.command is not None:
        command = ' '.join(args.command)
        shell.preloop()
        shell.onecmd(command)
    else:
        shell.cmdloop()
except KeyboardInterrupt:
    pass
