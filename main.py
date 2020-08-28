#!/usr/bin/env python3

'''
============== TODO ============================
add typing annotations everywhere
handle args: support primitives like str, int, bool, float
 - abstract complete folder
 - make it into reuseable separate package
file name argument parsing with special cases (TODO: test)
creating shortcuts (like R1, L4)

=============== Commands to add ================
mv, cp?
view
sysinfo
resource
pgrep, pkill
(upload|download)_dir

=============== nice to have(s) ================
Use libssh to prevent having to log in again for every command.
Having a ssh login every second might look very suspicious and has a bit of overhead

=============== Known Issues ===================
Remote commands using 'curses' (top, nano) do not work

=============== Command reminder ===============
Run (local only): /c/ssh-helper/main.py
Run with VM: /c/ssh-helper/main.py vagrant@172.28.128.3 -p vagrant
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
from src import SshSettings, MyShell, err, set_debug


parser = argparse.ArgumentParser(
    description='A SSH helper that is inspired by the Metasploit Meterpreter',
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('user_at_host', nargs='?', help='<SSH username>@<hostname/IP address>')
parser.add_argument('--password', '-p', help='SSH login password')
parser.add_argument('--command', '-c', nargs='+', help='run command and exit')
parser.add_argument('--debug', '-d', action='store_true', help='start with debug enabled')
args = parser.parse_args()

if args.debug:
    print('debug on')
    set_debug(True)

ssh_settings = None
if args.user_at_host:
    try:
        user, host = args.user_at_host.split('@')
        ssh_settings = SshSettings(host, user, args.password)
    except:
        print(err(f'Invalid format: "{args.user_at_host}"'))
        print('Expected format: "<SSH username>@<hostname/IP address>"')
        print('Examples: "admin@ssh.six-two.dev", "vagrant@172.28.128.3"')
        sys.exit(1)

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
