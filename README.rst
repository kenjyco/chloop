chloop
======

Install
-------

::

    % pip3 install chloop

The ``GetCharLoop`` class is provided by the ``chloop`` package. Calling
an **instance** of this class starts a REPL session, which the user can
end by pressing ``Ctrl`` + ``d`` or ``Ctrl`` + ``c``.

    See the **Example** section below.

Usage
-----

The **first** character you type at the REPL prompt is significant.

The colon
^^^^^^^^^

Hitting the ``:`` key at the prompt will allow you to enter a command
and any arguments you need to pass to that command.

-  ``:docstrings`` to view docstrings of methods defined on the class
-  ``:errors`` to view colon commands that raised exceptions
-  ``:history`` view colon commands issued
-  ``:pdb`` to start a pdb session (debugging/inspection)
-  ``:ipython`` to start ipython shell
-  ``:shortcuts`` to view hotkey shortcuts

Any methods added to your sub-class of ``GetCharLoop`` are callable as
**colon commands**, as long as they do not start with an underscore
(``_``). Methods should \*\*only accept \*args\*\*, if anything.

For any methods/commands that should not be logged to the history,
append the method name to the end of the ``self._DONT_LOG_CMDS`` list.

The dash
^^^^^^^^

Hitting the ``-`` key at the prompt will allow you to type a note.

Other keys
^^^^^^^^^^

Hitting any other key at the prompt will do one of the following:

-  call a **registered shortcut function** bound to the key (use
   ``:shortcuts`` command to see what is available)
-  display the character and its integer ordinal

To add new hotkey shortcuts, update the ``self._chfunc_dict`` object in
the ``__init__`` method of your subclass. The values for items in this
dictionary are 2-item tuples.

-  1st item is a **callable** that accepts no arguments
-  2nd item is a short help string

    Use ``functools.partial`` (if necessary) to create a callable
    accepting no arguments.

Basic example
-------------

::

    % python3 -c 'from chloop import GetCharLoop; GetCharLoop()()'

    > :docstrings
    ======================================================================
    Loop forever, receiving character input from user and performing actions

        - ^d or ^c to break the loop
        - ':' to enter a command (and any arguments)
            - the name of the command should be monkeypatched on the GetCharLoop
              instance, or be a defined method on a GetCharLoop sub-class
            - the function bound to `:command` should accept `*args` only
        - '-' to receive an input line from user (a note)

    .:: docstrings ::.
    Print/return the docstrings of methods defined on this class

    .:: errors ::.
    Print/return any colon commands that raised exceptions (w/ traceback)

    .:: history ::.
    Print/return colon commands used

    .:: ipython ::.
    Start ipython shell. To continue back to the input loop, use 'ctrl + d'

    .:: pdb ::.
    Start pdb (debugger). To continue back to the input loop, use 'c'

    .:: shortcuts ::.
    Print/return any hotkey shortcuts defined on this class



    > :pdb
    [10] > /tmp/ch/venv/lib/python3.5/site-packages/chloop/__init__.py(90)__call__()
    -> continue
    (Pdb++) l
     85                     cmd = user_input.split()[0]
     86                     args = user_input.split()[1:]
     87
     88                     if cmd == 'pdb':
     89                         import pdb; pdb.set_trace()
     90  ->                     continue
     91
     92                     if cmd == 'ipython':
     93                         from IPython import embed; embed()
     94                         continue
     95
    (Pdb++) self.collection
    Collection('chloop-log', 'default', index_fields='cmd,status,error_type', json_fields='args,value')
    (Pdb++) self.collection.keyspace
    []
    (Pdb++) c

    > :ipython
    Python 3.5.1+ (default, Mar 30 2016, 22:46:26)
    Type "copyright", "credits" or "license" for more information.

    IPython 5.2.2 -- An enhanced Interactive Python.
    ?         -> Introduction and overview of IPython's features.
    %quickref -> Quick reference.
    help      -> Python's own help system.
    object?   -> Details about 'object', use 'object??' for extra details.


    In [1]: self.collection
    Out[1]: Collection('chloop-log', 'default', index_fields='cmd,status,error_type', json_fields='args,value')

    In [2]: self.shortcuts
    Out[2]: <bound method GetCharLoop.shortcuts of <chloop.GetCharLoop object at 0x7f9f8ff5f5f8>>

    In [3]: self.docstrings
    Out[3]: <bound method GetCharLoop.docstrings of <chloop.GetCharLoop object at 0x7f9f8ff5f5f8>>

    In [4]:
    Do you really want to exit ([y]/n)? y


    > :shortcuts


    > - there are no shortcuts defined by default

    >

Example (sub-class)
-------------------

Import ``GetCharLoop`` and sub-class it
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    from functools import partial
    from chloop import GetCharLoop

    class Mine(GetCharLoop):
        """A sub-class of GetCharLoop"""
        def __init__(self, *args, **kwargs):
            # Process any extra/custom kwargs here and set some attributes
            self.thing = kwargs.pop('mything', 'some default value')

            super(Mine, self).__init__(*args, **kwargs)

            # Add some single-key shorcuts that call methods on `self`
            self._chfunc_dict.update({
                'h': (self.history,
                      'display recent command history'),
                'e': (self.errors,
                      'display recent errors'),
            })

        def somefunc(self, *args):
            """Does something"""
            args_as_one = ' '.join(args)
            print repr(args_as_one)
            return args_as_one

        def lame(self):
            """raise exception"""
            return 1/0

Initialize the sub-class and call it
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    if __name__ == '__main__':
        m = Mine(prompt='\nmyprompt> ')
        m()

Interact with the REPL
^^^^^^^^^^^^^^^^^^^^^^

    Assuming the above code is in a file called ``main.py``

::

    % python main.py

    myprompt> :somefunc here are some args
    u'here are some args'

    myprompt> :shortcuts
    'e' -- display recent errors
    'h' -- display recent command history

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

    myprompt> :pdb
    ...

    myprompt> e
    (errors output)

    myprompt> - here is a note

    myprompt> - here is another note

    myprompt>
