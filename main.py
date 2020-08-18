#!/usr/bin/env python3
import os
import sys

'''
TODO:
add typing annotations
antomatic help generation: parse the usage docstrings
(l)rm(dir)
(upload|download)_dir
file name argument parsing
argument count macro
'''

'''
=============== Command reminder ===============
Run: /c/ssh-helper/main.py
Run typechecker: mypy /c/ssh-helper/
'''

if __name__ == '__main__':
    # Change current dir to enable loading the other files
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
    sys.path.append(src_dir)
    # pylint: disable=import-error
    from ssh_command_builder import SshCommandConverter
    from my_shell import MyShell


    if "-h" in sys.argv or "--help" in sys.argv:
        MyShell(SshCommandConverter('should_never_be_used', 'should_never_be_used')).do_help('')
        sys.exit()

    # Default settings for metasploitable 3 (ubuntu 14.04)
    ssh_helper = SshCommandConverter("172.28.128.3", "vagrant", "vagrant")
    shell = MyShell(ssh_helper)
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        pass
