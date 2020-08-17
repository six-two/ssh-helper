from common import *

class SshCommandConverter:
    def __init__(self, remote_host, remote_user, remote_password=None):
        self.remote_username = remote_user
        self.remote_password = remote_password
        self.remote_host = remote_host

    def make_remote_command(self, command, ssh_options=[]):
        complete_command = []
        if self.remote_password:
            complete_command += ['sshpass', '-p', self.remote_password]

        ssh_user = '{}@{}'.format(self.remote_username, self.remote_host)
        complete_command += ['ssh', *ssh_options, ssh_user]
        complete_command += command
        return complete_command

    def make_scp_command(self, src, dst, is_upload, is_directory):
        remote_prefix = '{}@{}:'.format(self.remote_username, self.remote_host)
        if is_upload:
            dst = remote_prefix + dst
        else:
            src = remote_prefix + src

        complete_command = []
        if self.remote_password:
            complete_command += ['sshpass', '-p', self.remote_password]

        complete_command += ['scp', '-p']
        if is_directory:
            complete_command += ['-r']
        complete_command += [src, dst]

