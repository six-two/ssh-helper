# ssh-helper

An ssh wrapper that has a interface similar to Meterpreter

## Requirements

- Python 3.5+
- pip3 (to install needed libraries)
- ssh
- scp (for file transfer)
- sshpass (only if you use a password to log in)

### Arch Linux

You can install the dependencies by running the following command:

```
sudo pacman -S --needed python python-pip ssh scp sshpass
```

## Installation

```
python -m pip install git+https://github.com/six-two/py_derive_cmd
git clone https://github.com/six-two/ssh-helper
cd ssh-helper
python -m pip install -r requirements.txt
```

