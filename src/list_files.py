# pylint: disable=unused-wildcard-import
import traceback
import shlex
from typing import List, Sequence
# Local modules
from .common import *
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

'''
Idea: different commands give different outputs:
lsp (permission and ownership)
lsc/lst (sort by date changed)
lsl (all info)
lss (sort by size)
lsd (only dirs)
lsf (only files)

Idea: use rewrite lsds -> ls d s / ls ds
'''

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

