chloop is a Redis-backed character-driven REPL framework designed for developers who want to build custom interactive tools quickly and efficiently while providing progressive complexity. The library optimizes for single-keystroke efficiency while also leveraging vim's colon command paradigm to transform command-line interactions from sequential operations into immediate context-aware experiences.

The core philosophy centers on **cognitive load reduction through muscle memory development**. Instead of forcing users to remember complex command syntax or navigate menus, chloop enables the creation of interfaces where common actions become instinctive single keystrokes, while advanced functionality remains accessible through discoverable colon commands.

**Who benefits from this library:**
- **Domain experts** who need immediate control over complex systems (audio/video exploration, API testing, data analysis)
- **Interactive application developers** building tools for power users who value efficiency over discovery
- **CLI tool creators** who want to provide both accessibility for beginners and efficiency for experts
- **Content analysts** needing distraction-free, keyboard-driven workflows for media exploration
- **Researchers** who need to rapidly navigate and annotate large datasets or media collections

Real-world implementations include the **mocp-cli** package for interactive audio exploration with timestamp marking, and **vlc-helper** for precise video control and screenshot capture, demonstrating chloop's effectiveness in media analysis workflows.

## Install

If you don't have [docker](https://docs.docker.com/get-docker) installed, install Redis and start server

```
sudo apt-get install -y redis-server
```

or

```
brew install redis
brew services start redis
```

Install with `pip`

```
pip install chloop
```

> Optionally install ipython with `pip install ipython` to enable `:ipython` colon command on a GetCharLoop instance. Also `pip install pdbpp` for an improved debug experience when using `:pdb` colon command.

## QuickStart

The `GetCharLoop` class is provided by the `chloop` package. Calling an **instance** of this class starts a REPL session, which the user can end by pressing `Ctrl` + `d` or `Ctrl` + `c`.

The **first** character you type at the REPL prompt is significant.

### The colon

Hitting the `:` key at the prompt will allow you to enter a command and any arguments you need to pass to that command.

- `:docstrings` to view docstrings of methods defined on the class
- `:errors` to view colon commands that raised exceptions
- `:history` view colon commands issued
- `:pdb` to start a pdb session (debugging/inspection)
- `:ipython` to start ipython shell
- `:shortcuts` to view hotkey shortcuts

Any methods added to your sub-class of `GetCharLoop` are callable as **colon commands**, as long as they do not start with an underscore (`_`). Methods should **only accept `*args`**, if anything.

> For any methods/commands that should not be logged to the history, append the method name to the end of the `self._DONT_LOG_CMDS` list.

### The dash

Hitting the `-` key at the prompt will allow you to type a note.

### The question mark

Hitting the `?` key at the prompt will display the class docstring(s) and the startup message.

Hitting the `?` key a second time will show the available colon commands and shortcuts (equivalent to issuing `:docstrings` and `:shortcuts`)

### Other keys

Hitting any other key at the prompt will do one of the following:

- call a **registered shortcut function** bound to the key (use `:shortcuts`
  command to see what is available)
- display the character and its integer ordinal

A hotkey can be bound to any callable object that accepts no arguments. Use `functools.partial` (if necessary) to create a callable accepting no arguments.







### Basic example

> The default prompt if none is specified is `> `.

```
% python3 -c 'from chloop import GetCharLoop; GetCharLoop()()'

> ?
 Loop forever, receiving character input from user and performing actions

    - ctrl+d or ctrl+c to break the loop
    - ':' to enter a command (and any arguments)
        - any method defined on GetCharLoop (or a sub-class) will be callable
          as a "colon command" (if its name does not start with '_')
        - the method for the `:command` should only accept `*args`
    - '-' to allow user to provide input that will be processed by the `input_hook`
    - '?' to show class doc and the startup message
    - '??' to show class doc, the startup message, docstrings (:commands), and shortcuts

:docstrings to see all colon commands
:shortcuts to see all hotkeys


> :docstrings
.:: chars ::.
Show chars (hotkeys) pressed during current session

.:: cmds ::.
Show colon commands typed during current session

.:: docstrings ::.
Print/return the docstrings of methods defined on this class

.:: errors ::.
Print/return any colon commands that raised exceptions (w/ traceback)

.:: history ::.
Print/return successful colon commands used (default 10)

.:: ipython ::.
Start ipython shell. To continue back to the input loop, use 'ctrl + d'

.:: pdb ::.
Start pdb (debugger). To continue back to the input loop, use 'c'

.:: shortcuts ::.
Print/return any hotkey shortcuts defined on this class

.:: wishlist ::.
Show the wishlist (of hotkeys and commands that don't exist yet)
```

### Sub-class example

- Import `GetCharLoop` and sub-class it
- Initialize the sub-class and call it

> Save the following to `mine.py`

```
from functools import partial
from chloop import GetCharLoop


class Mine(GetCharLoop):
    """A sub-class of GetCharLoop"""
    def __init__(self, *args, **kwargs):
        # Process any extra/custom kwargs here and set some attributes
        self._mything = kwargs.pop('mything', 'some default value')

        super(Mine, self).__init__(*args, **kwargs)

        # Add some single-key shorcuts that call methods on `self`
        self._chfunc_dict_update([
            ('h', (self.history,
                  'display recent command history')),
            ('e', (self.errors,
                  'display recent errors')),
        ])


    def somefunc(self, *args):
        """Joins the args passed to it into a string"""
        args_as_one = ' '.join(args)
        print(repr(args_as_one))
        return args_as_one

    def lame(self):
        """raise exception"""
        return 1/0


if __name__ == '__main__':
    m = Mine(prompt='\nmyprompt> ')
    m._add_hotkey('a', lambda: print('hello'), 'say hello')
    m()
```

> Assuming the above code is in a file called `mine.py`

```
% python mine.py

myprompt> :somefunc here are some args
u'here are some args'

myprompt> :shortcuts
'e' -- display recent errors
'h' -- display recent command history
'a' -- say hello

myprompt> a
hello

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

```

### Extended example

> This example shows a subset of actual functionality from mocp-cli and assumes the moc wrapper is avaialbe.

```python
from functools import partial
from collections import OrderedDict
from chloop import GetCharLoop
import moc


class SimpleMusicPlayer(GetCharLoop):
    """Simplified music player interface using MOC backend"""

    def seek(self, num):
        """Seek forward or backward by specified seconds"""
        moc.seek(int(num))

    def go(self, timestamp):
        """Jump to a particular timestamp"""
        moc.go(timestamp)

    def find(self, *glob_patterns):
        """Find and select audio files at specified glob patterns"""
        moc.find_select_and_play(*glob_patterns)


shortcuts = OrderedDict([
    (' ', (moc.toggle_pause, 'pause/unpause')),
    ('i', (lambda: print(moc.info_string()), 'show info about currently playing file')),
    ('f', (partial(moc.find_and_play, '.'), 'find and play audio files found in current directory')),
    ('F', (partial(moc.find_select_and_play, '.'), 'find, select, and play audio files found in current directory')),
    ('Q', (moc.stop_server, 'stop MOC server and quit')),
    ('n', (moc.next, 'next file in playlist')),
    ('p', (moc.previous, 'previous file in playlist')),
    ('H', (partial(moc.seek, -30), 'rewind 30 seconds')),
    ('h', (partial(moc.seek, -5), 'rewind 5 seconds')),
    ('L', (partial(moc.seek, 30), 'fast forward 30 seconds')),
    ('l', (partial(moc.seek, 5), 'fast forward 5 seconds')),
    ('j', (moc.volume_down, 'lower volume')),
    ('k', (moc.volume_up, 'raise volume')),
    ('q', (lambda: None, 'quit')),
])

# Create and start the music player interface
player = SimpleMusicPlayer(
    chfunc_dict=shortcuts,
    name='simple-music',
    prompt='music> ',
    break_chars=['q', 'Q']
)

if __name__ == '__main__':
    player()
```

Then after starting the repl:

```
music> :shortcuts
Space -- pause/unpause
i -- show info about currently playing file
f -- find and play audio files found in current directory
F -- find, select, and play audio files found in current directory
Q -- stop MOC server and quit
n -- next file in playlist
p -- previous file in playlist
H -- rewind 30 seconds
h -- rewind 5 seconds
L -- fast foward 30 seconds
l -- fast foward 5 seconds
j -- lower volume
k -- raise volume
q -- quit
```

## API Overview

### Core Class

- **`GetCharLoop(*args, **kwargs)`** - Main framework class for building character-driven interactive tools
  - `chfunc_dict`: OrderedDict mapping characters to (function, help_text) tuples for hotkeys
  - `prompt`: String to display when asking for input (default: `'\n> '`)
  - `name`: Value for Redis collection naming to isolate different tool instances
  - `break_chars`: List of characters that exit the loop (can trigger functions before exit)
  - `input_hook`: Callable receiving `**kwargs` to process user input after '-' key pressed
  - `pre_input_hook`: Callable receiving no args executed when `-` is pressed, returning dict of data to input_hook
  - `post_input_hook`: Callable receiving no args executed after input collection, returning dict of data  to input_hook
  - Returns: Configured GetCharLoop instance ready for direct use
  - Internal calls: `rh.Collection()`

### Primary Methods

- **`GetCharLoop.__call__()`** - Start the interactive character loop
  - Returns: None (runs until interrupted with Ctrl+C or Ctrl+D)
  - Internal calls: `ih.getchar()`, `self.docstrings()`, `self.shortcuts()`, `ih.user_input_fancy()`, `bh.call_func()`, `ih.user_input()`, `ih.start_ipython()`

### Built-in Commands

All public methods automatically become `:commands` through naming convention:

- **`GetCharLoop.docstrings(*args)`** - Display all available commands with their documentation
  - Returns: String containing formatted docstring output
  - Internal calls: None

- **`GetCharLoop.shortcuts(*args)`** - Show configured hotkey mappings and their descriptions
  - Returns: String containing formatted shortcut output
  - Internal calls: None

- **`GetCharLoop.history(*args)`** - Display recent successful commands
  - `*args` - Optional limit parameter (default 10)
  - Returns: None (prints formatted history)
  - Internal calls: `ih.from_string()`

- **`GetCharLoop.errors(*args)`** - Show recent command errors with full tracebacks
  - `*args` - Optional limit parameter (default 10)
  - Returns: None (prints formatted error output)
  - Internal calls: `ih.from_string()`

- **`GetCharLoop.chars()`** - Display characters pressed during current session
  - Returns: None (prints character history)
  - Internal calls: None

- **`GetCharLoop.cmds()`** - Show colon commands typed during current session
  - Returns: None (prints command history)
  - Internal calls: None

- **`GetCharLoop.wishlist()`** - Display captured user intent for non-existent commands and hotkeys
  - Returns: None (prints formatted wishlist)
  - Internal calls: None

### Special Commands

- **`:pdb`** - Launch Python debugger
- **`:ipython`** - Start IPython shell with `self` available for inspection

### Extension Methods

- **`GetCharLoop._add_hotkey(ch, func, help_string)`** - Register single-character hotkey
  - `ch`: Character to trigger the hotkey
  - `func`: Callable object accepting no arguments (use `functools.partial` if needed)
  - `help_string`: Description shown in `:shortcuts` output
  - Returns: None
  - Internal calls: None

- **`GetCharLoop._chfunc_dict_update(obj)`** - Bulk update hotkey mappings
  - `obj`: List of tuples or dict containing (character, (function, help_text)) mappings
  - Returns: None
  - Internal calls: None
