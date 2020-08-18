# pylint: disable=unused-wildcard-import
from typing import Sequence, List
# Local modules
from common import *


class SshSettings:
    def __init__(self, host: str, user: str, password: str = None) -> None:
        self.user = user
        self.host = host
        self.password = password

class SshCommandConverter:
    def __init__(self, ssh: SshSettings) -> None:
        self.user_at_host = f'{ssh.user}@{ssh.host}'
        self.sshpass = ['sshpass', '-p', ssh.password] if ssh.password else []

    def make_remote_command(self, command: Sequence[str], ssh_options: Sequence[str] = None) -> List[str]:
        if ssh_options is None:
            ssh_options = []
        return [*self.sshpass, 'ssh', *ssh_options, self.user_at_host, *command]

    def make_scp_command(self, src: str, dst: str, is_upload: bool, is_directory: bool) -> List[str]:
        if is_upload:
            dst = f'{self.user_at_host}:{dst}'
        else:
            src = f'{self.user_at_host}:{src}'

        scp_options = ['-p']
        if is_directory:
            scp_options.append('-r')

        return [*self.sshpass, 'scp', *scp_options, src, dst]

