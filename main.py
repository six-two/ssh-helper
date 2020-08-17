#!/usr/bin/env python3
import os
import sys
# Change current dir to enable loading the other files
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from ssh_command_builder import SshCommandConverter
from common import *
from my_shell import MyShell


if __name__ == '__main__':
    if "-h" in sys.argv or "--help" in sys.argv:
        print(USAGE)
        sys.exit()

    # Default settings for metasploitable 3 (ubuntu 14.04)
    ssh_helper = SshCommandConverter("172.28.128.3", "vagrant", "vagrant")
    shell = MyShell(ssh_helper)
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        pass
