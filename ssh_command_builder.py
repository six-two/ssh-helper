from common import *

class SshCommandConverter:
    def __init__(self, host, user, password=None):
        # self.username = user
        # self.password = password
        # self.host = host
        self.user_at_host = f'{user}@{host}'
        self.sshpass = ['sshpass', '-p', password] if password else []

    def make_remote_command(self, command, ssh_options=[]):
        return [*self.sshpass, 'ssh', *ssh_options, self.user_at_host, *command]

    def make_scp_command(self, src, dst, is_upload, is_directory):
        if is_upload:
            dst = f'{self.user_at_host}:{dst}'
        else:
            src = f'{self.user_at_host}:{src}'

        scp_options = ['-p']
        if is_directory:
            scp_options.append('-r')

        return [*self.sshpass, 'scp', *scp_options, src, dst]

