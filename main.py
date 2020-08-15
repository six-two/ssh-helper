#!/usr/bin/env python3
import subprocess

DEBUG = True


class Instance:
    def __init__(self, remote_host, remote_user, remote_password=None):
        self.local_path = None
        self.remote_path = None
        self.remote_username = remote_user
        self.remote_password = remote_password
        self.remote_host = remote_host

        # Todo: add error handling? Add remote timeouts?
        self.local_path = self.execute_local_command(["pwd"], run_in_background=True)[1].decode().strip()
        self.remote_path = self.execute_remote_command(["pwd"], run_in_background=True)[1].decode().strip()

    def execute_remote_command(self, command, run_in_background=False):
        complete_command = []
        if self.remote_password:
            complete_command += ['sshpass', '-p', self.remote_password]

        ssh_user = '{}@{}'.format(self.remote_username, self.remote_host)
        complete_command += ['ssh', ssh_user]
        if self.remote_path:
            complete_command += ['cd', self.remote_path, ';']
        complete_command += command
        return self.execute_local_command(complete_command, run_in_background)

    def execute_local_command(self, command, run_in_background=False):
        if DEBUG:
            print(command)
        options = {}
        if run_in_background:
            options['stdout'] = subprocess.PIPE
            options['stderr'] = subprocess.STDOUT

        result = subprocess.run(command, **options)
        output = result.stdout if run_in_background else None
        r = (result.returncode, output)
        if DEBUG:
            print(r)
        return r


if __name__ == '__main__':
    import json
    # Default settings for metasploitable 3 (ubuntu 14.04)
    i = Instance("172.28.128.3", "vagrant", "vagrant")
    print(json.dumps(i.__dict__))
    i.execute_remote_command(['ls', '-al'])
    i.remote_path = "/home"
    i.execute_remote_command(['ls', '-al'])
