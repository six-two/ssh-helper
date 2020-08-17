# External libraries. Might need no be installed via pip
import termcolor


_DEBUG = False

def err(message):
    '''Creates a colored string to be printed. It uses the standard error color'''
    return termcolor.colored(message, "red")

def is_debug():
    return _DEBUG

def print_debug(msg):
    if _DEBUG:
        print(msg)

def set_debug(new_value):
    global _DEBUG
    _DEBUG = new_value
