from typing import List, Sequence, Optional, Tuple, Any
from inspect import Parameter
import shlex
# Local
from .common import err, print_debug
from .complete import UsageException


def split_incomplete_args(incomplete_arg_str: str) -> List[str]:
    # add character to test if the last param should be extended
    # or if a new argument should be started
    TEST_STRING = '_new'
    before_cursor = incomplete_arg_str + TEST_STRING
    args = split_args(before_cursor, may_be_cut_off=True)
    # Remove TEST_STRING
    if args[-1] == TEST_STRING:
        # Keep the empty argument to complete
        args[-1] = ''
    elif args[-1].endswith(TEST_STRING):
        args[-1] = args[-1][:-len(TEST_STRING)]
    else:
        print('BUG: Argument parsing: WTF happened to the underscore?')

    print_debug(args)
    return args


def split_args(arg_str: str, may_be_cut_off=False) -> List[str]:
    if arg_str:
        return shlex.split(arg_str)
    else:
        return []

def parse_args(params: Sequence[Parameter], args: Sequence[str]) -> Optional[List]:
        parsed = []
        print_debug(f'before parse: {args}')
        for i in range(len(args)):
            # Get the class of the parameter
            param_cls = params[i].annotation
            arg: Any = args[i]

            if param_cls != Parameter.empty:
                try:
                    # Replace the argument with its parsed value
                    arg = param_cls(arg)
                except UsageException as ex:
                    # Print an error message and
                    print(err(f'Usage error in argument {i+1}: {ex}'))
                    return None
                print_debug(f'Param converted to {param_cls}')
            else:
                print_debug('Param {i}: No type in method signature')

            parsed.append(arg)

        print_debug(f'after parse: {parsed}')
        return parsed

def param_to_help_text(p: Parameter) -> str:
    name = p.name
    name = name.upper()
    optional = p.default != Parameter.empty
    return f'[{name}]' if optional else f'<{name}>'

def arg_counts(params: Sequence[Parameter]) -> Tuple[int, int]:
    max_args = len(params)
    min_args = 0
    for p in params:
        # Count how many arguments are required
        if p.default != Parameter.empty:
            break
        min_args += 1
    return (min_args, max_args)
