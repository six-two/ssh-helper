# pylint: disable=unused-wildcard-import
import traceback
import shlex
from typing import List, Sequence
# Local modules
from ..common import *
from ..my_shell import MyShell
from ..complete import LFile, RFile
# External libs
from tabulate import tabulate

class LsFileInfo:
    def __init__(self, line: str, shortcut: str = None) -> None:
        self.shortcut = shortcut
        parsed = shlex.split(line)
        self.perm, self.hard_links, self.owner, self.owner_group, size, self.date, self.time = parsed[:7]
        self.size = int(size)
        rest: List[str] = parsed[7:]

        if len(rest) == 0:
            raise Exception('No path')
        elif len(rest) == 1:
            self.path = rest[-1]
        elif rest[1] == '->':
            self.path = rest[0]
            if rest[-1].endswith('/'):
                self.path += '/'
        else:
            raise Exception(f'Unexpected path in ls output: {rest}')

    def is_dir(self) -> bool:
        return self.path.endswith('/')

    def shortened_path(self, max_length: int) -> str:
        if max_length < 8:
            raise Exception(f'max_langth={max_length} is to small')

        if len(self.path) > max_length:
            return self.path[:max_length - 3] + '...'
        else:
            return self.path

    def size_str(self) -> str:
        if self.size < 1024:
            return f'{self.size} B'
        else:
            num: float = self.size
            for unit in ['B','KiB','MiB','GiB','TiB']:
                if abs(num) < 1024.0:
                    return "%3.1f %s" % (num, unit)
                num /= 1024.0
            # Should not happen
            return str(num)

    def full_owner(self) -> str:
        return f'{self.owner}:{self.owner_group}'

    def date_time(self) -> str:
        return f'{self.date} {self.time}'

    @staticmethod
    def create_shortcut(remote: IsRemote, index: int) -> str:
        '''
        Idea:
        make alphabetic with flags:
        l: local
        d: dir (end flags)
        f: file (end flags)?
        '''
        host_specifier = '' if remote else 'l'
        return f'${host_specifier}{index}'

def list_files(executor, is_remote: IsRemote, path: str = None) -> List[LsFileInfo]:
    command = ['ls', '-Alb', '--time-style=long-iso', '--indicator-style=slash']
    if path:
        command += [path]

    output = executor.execute_in_background(is_remote, command)
    lines = [l for l in output.split('\n') if l]
    # remove the 'total ...' line
    if len(lines) > 1 and lines[0].startswith('total'):
        lines = lines[1:]

    return [LsFileInfo(l) for l in lines]

SORT_KEY_FUNCTIONS = {
    '': lambda x: x.path,
    't': lambda x: x.date_time(),
    's': lambda x: x.size,
    'p': lambda x: (x.owner, x.owner_group),
}

def print_ls(files: Sequence[LsFileInfo], filters: str, sort_by: str, columns: str) -> None:
    '''
    Filters:
        d: directories only
        f: files only
        '': no filtering

    Sorting by:
        t: time changed
        s: size
        p: (owner, group)
        '': name

    Columns:
        '', t, s: name, size, time changed
        p: name, permission, owner, group
        l: name, size, permission, owner:group, time changed
    '''
    # Filter
    if filters:
        if filters == 'd':
            files = [x for x in files if x.is_dir()]
        elif filters == 'f':
            files = [x for x in files if not x.is_dir()]
        else:
            raise Exception(f'Unknown filter: "{filter}"')

    # Sort
    fn_sort_key = SORT_KEY_FUNCTIONS[sort_by]
    # Assuming that the sorting algorithm is stable: order equal elements by name
    files = sorted(files, key=lambda x: x.path)
    # Order by given metric
    files = sorted(files, key=fn_sort_key)

    # Save some space when using the long format
    max_path_length = 40 if columns == 'l' else 80

    # Print
    data: List[tuple] = []
    if columns in ['', 't', 's']:
        data.append(('Filename', 'Size', 'Last modified'))
        for f in files:
            data.append((f.shortened_path(max_path_length), f.size_str(), f.date_time()))
    elif columns == 'p':
        data.append(('Filename', 'Permissions', 'Owner', 'Group'))
        for f in files:
            data.append((f.shortened_path(max_path_length), f.perm, f.owner, f.owner_group))
    elif columns == 'l':
        data.append(('Filename', 'Size', 'Permissions', 'Owner:group', 'Last modified'))
        for f in files:
            data.append((f.shortened_path(max_path_length), f.size_str(), f.perm, f.full_owner(), f.date_time()))

    print(tabulate(data, headers='firstrow', tablefmt='presto'))
    # print('\nHint: You can use a shortcut to refer to a file.')
        # TODO pad
        # line = f'{shortcut} {line}'

        # print(line)


def _internal_ls_formated(my_shell: MyShell, is_remote: IsRemote, flags: str, path: str):
    format_flag = ''
    filters = ''
    sort_by = ''
    for flag in flags:
        if flag == 'l':
            if format_flag:
                print(warn(f'Ignored format flag "{flag}", because the format is already set to "{format_flag}"'))
            else:
                format_flag = flag
        elif flag in ['s', 'p', 't']:
            if sort_by:
                print(warn(f'Ignored sorting flag "{flag}", because the sorting is already set to "{sort_by}"'))
            else:
                sort_by = flag
        elif flag in ['f', 'd']:
            if filters:
                print(warn(f'Ignored filter flag "{flag}", because the filter is already set to "{filters}"'))
            else:
                filters = flag
        else:
            print(err(f'Unknown flag: "{flag}"'))

    if not format_flag:
        format_flag = sort_by

    files = list_files(my_shell.executor, is_remote, path)
    print_ls(files, filters, sort_by, format_flag)

settings = get_settings()

@make_command(settings, 'List local files')
def lls(my_shell: MyShell, path: LFile = LFile('.')) -> None:
    '''List the files in the current directory or in the given path on the local computer'''
    _internal_ls_formated(my_shell, LOCAL, '', path.value())

@make_command(settings, 'List local files')
def lls_format(my_shell: MyShell, flags: str, path: LFile = LFile('.')) -> None:
    '''List the files in the current directory or in the given path on the local computer'''
    _internal_ls_formated(my_shell, LOCAL, flags, path.value())

@make_command(settings, 'List remote files')
def ls(my_shell: MyShell, path: RFile = RFile('.')) -> None:
    '''List the files in the current directory or in the given path on the remote computer'''
    _internal_ls_formated(my_shell, REMOTE, '', path.value())

@make_command(settings, 'List remote files')
def ls_format(my_shell: MyShell, flags: str, path: RFile = RFile('.')) -> None:
    '''List the files in the current directory or in the given path on the remote computer'''
    _internal_ls_formated(my_shell, REMOTE, flags, path.value())

