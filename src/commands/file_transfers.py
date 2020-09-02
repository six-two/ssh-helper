# pylint: disable=unused-wildcard-import
import os
# Local
from ..common import *
from ..my_shell import MyShell
from ..executor import NoRemoteException
from ..complete import *
from .misc import run


def file_transfer(my_shell: MyShell, src: str, dst: str, is_upload: bool, is_directory: bool) -> None:
    ssh_helper = my_shell.executor.ssh_helper

    if not ssh_helper:
        raise NoRemoteException()

    command = ssh_helper.make_scp_command(src, dst, is_upload, is_directory)
    my_shell.executor.execute(LOCAL, command)


settings = get_settings()

@make_command(settings, 'Download a remote file', aliases=['dl'])
def download(my_shell: MyShell, path: RFile) -> None:
    '''Download the file located at path from the local computer and saves it with the same filename in the working directory on the local computer.'''
    remote_path = path.value()
    local_path = os.path.basename(remote_path)
    is_upload = False
    is_directory = False
    file_transfer(my_shell, remote_path, local_path, is_upload, is_directory)

@make_command(settings, 'Upload a local file', aliases=['ul'])
def upload(my_shell: MyShell, path: LFile) -> None:
    '''Upload the file located at path from the local computer and saves it with the same filename in the working directory on the remote computer.'''
    local_path = path.value()
    remote_path = os.path.basename(local_path)
    is_upload = True
    is_directory = False
    file_transfer(my_shell, remote_path, local_path, is_upload, is_directory)

@make_command(settings, 'Upload local file and execute on remote', aliases=['ulx'])
def upload_and_run(my_shell: MyShell, path: LFile) -> None:
    '''Mark the given file as executeable and then execute it'''
    file_name = RFile(os.path.basename(path.value()))

    upload(my_shell, path)
    run(my_shell, file_name)

