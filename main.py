#!/usr/bin/env python3
import subprocess

DEBUG = False


class SshCommandConverter:
    def __init__(self, remote_host, remote_user, remote_password=None):
        self.remote_username = remote_user
        self.remote_password = remote_password
        self.remote_host = remote_host

    def make_remote_command(self, command):
        complete_command = []
        if self.remote_password:
            complete_command += ['sshpass', '-p', self.remote_password]

        ssh_user = '{}@{}'.format(self.remote_username, self.remote_host)
        complete_command += ['ssh', ssh_user]
        complete_command += command
        return complete_command


def execute_local_command(command, run_in_background=False, cwd=None):
    if DEBUG:
        print(command)
    options = {}
    options['cwd'] = cwd
    if run_in_background:
        options['stdout'] = subprocess.PIPE
        options['stderr'] = subprocess.STDOUT

    result = subprocess.run(command, **options)
    output = result.stdout if run_in_background else None
    r = (result.returncode, output)
    if DEBUG:
        print(r)
    return r


class Instance:
    def __init__(self, remote_host, remote_user, remote_password=None):
        self.local_path = None
        self.remote_path = None
        self.ssh_helper = SshCommandConverter(remote_host, remote_user, remote_password)

        self.local_path = self.pwd()
        self.remote_path = self.pwd(remote=True)

    def execute_command(self, command, remote=False, run_in_background=False):
        if remote:
            if self.remote_path:
                command = ['cd', self.remote_path, ';'] + command
            command = self.ssh_helper.make_remote_command(command)
        return execute_local_command(command,
                                     run_in_background=run_in_background,
                                     cwd=self.local_path)

    def pwd(self, remote=False):
        # Todo: add error handling? Add remote timeouts?
        status, output = self.execute_command(["pwd"], run_in_background=True)
        if status != 0:
            raise Exception('Process exited with code {}'.format(status))
        return output.decode().strip()

    def cwd(self, remote=False):
        return self.remote_path if remote else self.local_path

    def ls(self, path=None, remote=False):
        command = ['ls', '-Alg']
        if path:
            command += [path]

        status, output = self.execute_command(command, run_in_background=True)
        if status != 0:
            raise Exception('Process exited with code {}'.format(status))
        # TODO only show useful columns
        output = output.decode()
        output = output.split('\n', 1)[1]  # remove the 'total=...' line
        print(output)


if __name__ == '__main__':
    # Default settings for metasploitable 3 (ubuntu 14.04)
    i = Instance("172.28.128.3", "vagrant", "vagrant")

    # i.execute_command(['ls', '-al'], remote=True)
    i.remote_path = "/home"
    i.ls(remote=True)
    # i.execute_command(['ls', '-al'])
    i.local_path = "/home"
    i.ls()
    i.ls("/tmp")
