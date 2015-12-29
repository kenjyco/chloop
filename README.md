chloop
======

A Redis-backed REPL that saves command history, output, & errors.

## Install

```
% virtualenv env
% env/bin/pip install git+git://github.com/kenjyco/chloop.git
% source env/bin/activate
```

The `GetCharLoop` class is provided by the `chloop` package. Calling an
**instance** of this class starts a REPL session, which the user can end by
pressing `Ctrl` + `d` or `Ctrl` + `c`.

> See the **Example** section below.

## Usage

The **first** character you type at the REPL prompt is significant.

#### The colon

Hitting the `:` key at the prompt will allow you to enter a command and any
arguments you need to pass to that command.

- `:docstrings` to view docstrings of methods defined on the class
- `:errors` to view colon commands that raised exceptions
- `:history` view colon commands issued during this session
- `:indices` to show all Redis indicies (for fields of hashes)
- `:ipdb` to start an ipdb session (debugging/inspection)
- `:session_keys` to show Redis keys for current session
- `:session_notes` to view notes created in current session
- `:shortcuts` to view hotkey shortcuts

Any methods added to your sub-class of `GetCharLoop` are callable as **colon
commands**, as long as they do not start with an underscore (`_`). Methods
should **only accept *args**, if anything.

For any methods/commands that should not be logged to the history, append the
method name to the end of the `self._DONT_LOG_CMDS` list.

#### The dash

Hitting the `-` key at the prompt will allow you to type a note.

> Use the `:session_notes` command to view any notes added, with timestamps.

#### Other keys

Hitting any other key at the prompt will do one of the following:

- call a **registered shortcut function** bound to the key (use `:shortcuts`
  command to see what is available)
- display the character and its integer ordinal

To add new hotkey shortcuts, update the `self._chfunc_dict` object in the
`__init__` method of your subclass. The values for items in this dictionary are
2-item tuples.

- 1st item is a **callable** that accepts no arguments
- 2nd item is a short help string

> Use `functools.partial` (if necessary) to create a callable accepting no
> arguments.

## Example

#### Import `GetCharLoop` and sub-class it

```
from functools import partial
from chloop import GetCharLoop

class Mine(GetCharLoop):
    """A sub-class of GetCharLoop"""
    def __init__(self, *args, **kwargs):
        # Process any extra/custom kwargs here and set some attributes
        if 'mything' in kwargs:
            self.thing = kwargs.pop('mything')
        else:
            self.thing = 'some default value'

        super(Mine, self).__init__(*args, **kwargs)

        # Add some single-key shorcuts that call methods on `self`
        self._chfunc_dict.update({
            'k': (partial(self.session_keys, display=True),
                  'show redis keys for current session'),
            'n': (partial(self.session_notes, display=True),
                  'show notes for current session'),
            'h': (self.history,
                  'display command history for current session'),
            'e': (self.errors,
                  'display errors for current session'),
        })

    def somefunc(self, *args):
        """Does something"""
        args_as_one = ' '.join(args)
        print repr(args_as_one)
        return args_as_one

    def lame(self):
        """raise exception"""
        return 1/0
```

#### Initialize the sub-class and call it

```
if __name__ == '__main__':
    m = Mine(prefix='myrediskeyspace', prompt='\nmyprompt> ')
    m()
```

#### Interact with the REPL

> Assuming the above code is in a file called `main.py`

```
% python main.py

myprompt> :somefunc here are some args
u'here are some args'

myprompt> :shortcuts
'e' -- display errors for current session
'h' -- display command history for current session
'k' -- show redis keys for current session
'n' -- show notes for current session

myprompt> h
Command history for 'myrediskeyspace:Mine:1000'

----------------------------------------------------------------------
myrediskeyspace:Mine:1000:cmd_results:1000
{'args': "[u'here', u'are', u'some', u'args']",
 'cmd': 'somefunc',
 'value': 'here are some args'}

myprompt> :lame
======================================================================
Traceback (most recent call last):
  File "/home/ken/chloop/chloop/__init__.py", line 232, in __call__
    value = cmd_func()
  File "main.py", line 33, in lame
    return 1/0
ZeroDivisionError: integer division or modulo by zero

cmd: u'lame'
args: []

myprompt> :ipdb
> /home/ken/chloop/chloop/__init__.py(220)__call__()
    219                     import ipdb; ipdb.set_trace()
--> 220                     continue
    221

ipdb> self.thing
'some default value'

ipdb> pp self._redis.hgetall('myrediskeyspace:Mine:1000:error:1000')
{'error_type': "<type 'exceptions.ZeroDivisionError'>",
 'error_value': "ZeroDivisionError('integer division or modulo by zero',)",
 'fqdn': 'kenjyco',
 'func': 'lame',
 'func_args': '[]',
 'func_doc': 'raise exception',
 'func_module': '__main__',
 'time_epoch': '1451362157.572994',
 'time_string': '2015_1228-Mon-220917',
 'traceback_string': 'Traceback (most recent call last):\n  File "/home/ken/chloop/chloop/__init__.py", line 220, in __call__\n    continue\n  File "main2.py", line 35, in lame\n    return 1/0\nZeroDivisionError: integer division or modulo by zero\n'}
ipdb>
ipdb> c

myprompt> e
Command errors for 'myrediskeyspace:Mine:1000'
----------------------------------------------------------------------
myrediskeyspace:Mine:1000:error:1000
{'error_type': "<type 'exceptions.ZeroDivisionError'>",
 'error_value': "ZeroDivisionError('integer division or modulo by zero',)",
 'fqdn': 'kenjyco',
 'func': 'lame',
 'func_args': '[]',
 'func_doc': 'raise exception',
 'func_module': '__main__',
 'time_epoch': '1451362157.572994',
 'time_string': '2015_1228-Mon-220917'}

Traceback (most recent call last):
  File "/home/ken/chloop/chloop/__init__.py", line 220, in __call__
    continue
  File "main.py", line 35, in lame
    return 1/0
ZeroDivisionError: integer division or modulo by zero


myprompt> - here is a note

myprompt> - here is another note

myprompt> n
Notes for 'myrediskeyspace:Mine:1000:notes0'
- 2015_1228-Mon-223345: here is a note
- 2015_1228-Mon-223350: here is another note


myprompt>
```
