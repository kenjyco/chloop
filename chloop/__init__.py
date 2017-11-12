import inspect
import click
import logging
import os.path
import input_helper as ih
import bg_helper as bh
import redis_helper as rh
from io import StringIO
from collections import OrderedDict
from pprint import pprint


LOGFILE = os.path.abspath('log--chloop.log')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOGFILE, mode='a')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(funcName)s: %(message)s'
))
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
logger.addHandler(file_handler)
logger.addHandler(console_handler)


class GetCharLoop(object):
    """Loop forever, receiving character input from user and performing actions

    - ctrl+d or ctrl+c to break the loop
    - ':' to enter a command (and any arguments)
        - any method defined on GetCharLoop (or a sub-class) will be callable
          as a "colon command" (if its name does not start with '_')
        - the method for the `:command` should only accept `*args`
    - '-' to allow user to provide input that will be processed by the `input_hook`
    - '?' to show the class docstring(s) and the startup message
    """
    _startup_message = ':docstrings to see all colon commands\n:shortcuts to see all hotkeys\n'

    def __init__(self, *args, **kwargs):
        """

        kwargs:

        - chfunc_dict: an OrderedDict where keys are characters and values are
          2-item tuples
            - first item is a function accepting no arguments
                - use `functools.partial` if needed
            - second item is some 'help text'
        - prompt: string to display when asking for input (default is '\n> ')
        - name: value of the 'name' argument for `redis_helper.Collection`
        - break_chars: list of characters that can be used to break the loop
            - if any char is used in chfunc_dict, the associated function will
              be called before breaking the input loop
        - input_hook: a callable (that receives `**kwargs`) to do extra things
          with user input received after '-' is pressed
            - the dict returned from the `input_helper.user_input_fancy` func
              will be used as kwargs to the `input_hook`
        - pre_input_hook: a callable (receiving no args) that returns a dict of
          info (as soon as '-' is pressed) that will be passed to `input_hook`
        - post_input_hook: a callable (receiving no args) that returns a dict of
          info (as soon as user_input_fancy completes) that will be passed to
          `input_hook`
        """
        self._chfunc_dict = kwargs.pop('chfunc_dict', OrderedDict())
        self._prompt = kwargs.pop('prompt', '\n> ')
        self._loop_name = kwargs.pop('name', 'default')
        self._break_chars = kwargs.pop('break_chars', [])
        self._input_hook = kwargs.pop('input_hook', None)
        self._pre_input_hook = kwargs.pop('pre_input_hook', None)
        self._post_input_hook = kwargs.pop('post_input_hook', None)
        self._DONT_LOG_CMDS = [
            'docstrings', 'shortcuts', 'errors', 'history',
        ]
        self._collection = rh.Collection(
            'chloop-log',
            self._loop_name,
            index_fields='cmd,status,error_type',
            json_fields='args,value'
        )

        self._method_names = [
            m[0]
            for m in inspect.getmembers(self) if not m[0].startswith('_')
        ]
        self._method_docs = {
            method: getattr(self, method).__doc__ or ''
            for method in self._method_names
        }

        if type(self._chfunc_dict) != OrderedDict:
            self._chfunc_dict = OrderedDict(sorted(
                self._chfunc_dict.items(),
                key=lambda k: k[1][1]
            ))

    def __call__(self):
        print(self._startup_message)
        while True:
            click.secho(self._prompt, nl=False, fg='cyan', bold=True)
            try:
                ch = click.getchar()
            except (EOFError, KeyboardInterrupt):
                break
            else:
                if ch in ['\x03', '\x04']:
                    break

            if ch == '?':
                print('?\n', self._class_doc())
                print(self._startup_message)
            elif ch == '-':
                try:
                    if self._pre_input_hook:
                        pre_input_data = self._pre_input_hook()
                    else:
                        pre_input_data = {}
                    user_input = ih.user_input_fancy('', '- ')
                    if self._post_input_hook:
                        post_input_data = self._post_input_hook()
                    else:
                        post_input_data = {}
                    if self._input_hook:
                        bh.call_func(
                            self._input_hook,
                            **user_input,
                            **pre_input_data,
                            **post_input_data,
                            logger=logger
                        )
                    else:
                        self._collection.add(
                            cmd='-',
                            user_input=user_input['text'],
                            status='ok',
                            **pre_input_data,
                            **post_input_data
                        )
                except click.exceptions.Abort:
                    print()
                    continue
            elif ch == ':':
                try:
                    user_input = click.prompt(text='', prompt_suffix=':', default='', show_default=False)
                except click.exceptions.Abort:
                    print()
                    continue
                else:
                    if not user_input:
                        print()
                        continue
                cmd = user_input.split()[0]
                args = user_input.split()[1:]

                if cmd == 'pdb':
                    import pdb; pdb.set_trace()
                    continue

                if cmd == 'ipython':
                    from IPython import embed; embed()
                    continue

                try:
                    cmd_func = getattr(self, cmd)
                except AttributeError:
                    self._collection.add(cmd=cmd, status='error', error_type='invalid command')
                    logger.error('invalid command: {}'.format(cmd))
                    continue

                info = bh.call_func(cmd_func, *args, logger=logger)
                info['cmd'] = cmd
                if cmd in self._DONT_LOG_CMDS:
                    info = {}

                if info:
                    self._collection.add(**info)
            elif ch in self._chfunc_dict:
                print(ch)
                bh.call_func(self._chfunc_dict[ch][0], logger=logger)
                if ch in self._break_chars:
                    break
            elif ch in self._break_chars:
                print(ch)
                break
            else:
                try:
                    print(repr(ch), ord(ch))
                except TypeError:
                    # ord() expected a character, but string of length 2 found
                    #   - happens if you press 'Esc' before another key
                    print(repr(ch))

    def pdb(self):
        """Start pdb (debugger). To continue back to the input loop, use 'c'"""
        # This function is actually never called, only added for the docstring
        pass

    def ipython(self):
        """Start ipython shell. To continue back to the input loop, use 'ctrl + d'"""
        # This function is actually never called, only added for the docstring
        pass

    def _chfunc_dict_update(self, obj):
        """Update the self._chfunc_dict OrderedDict

        - obj: a list of tuples or a dict
        """
        if type(obj) == dict:
            self._chfunc_dict.update(sorted(
                obj.items(),
                key=lambda k: k[1]
            ))
        else:
            self._chfunc_dict.update(obj)

    def _add_hotkey(self, ch, func, help_string):
        """Update the self._chfunc_dict OrderedDict

        - ch: character hotkey
        - func: callable object that accepts no arguments
        - help_string: a string containing short help text for hotkey
        """
        assert callable(func), 'func must be callable!'
        self._chfunc_dict[ch] = (func, help_string)

    def _class_doc(self):
        """Return a cumulative docstring for class and parent classes"""
        docs = []
        for cls in inspect.getmro(self.__class__):
            docs.append(cls.__doc__ or '')
            if cls.__name__ == 'GetCharLoop':
                break
        docs = reversed([d.strip() for d in docs if d])
        return '\n\n'.join(docs) + '\n'

    def docstrings(self, *args):
        """Print/return the docstrings of methods defined on this class"""
        fp = StringIO()

        for method, docstring in sorted(self._method_docs.items()):
            if docstring:
                fp.write('.:: {} ::.\n{}\n\n'.format(method, docstring.strip()))
            else:
                fp.write('.:: {} (no docs) ::.\n\n'.format(method))

        text = fp.getvalue()
        print(text)
        return text

    def shortcuts(self, *args):
        """Print/return any hotkey shortcuts defined on this class"""
        fp = StringIO()
        if self._chfunc_dict:
            for ch in self._chfunc_dict:
                line = '{} -- {}\n'.format(
                    ih.CH2NAME.get(ch, repr(ch)),
                    self._chfunc_dict[ch][1]
                )
                fp.write(line)

        text = fp.getvalue()
        print(text)
        return text

    def errors(self, *args):
        """Print/return any colon commands that raised exceptions (w/ traceback)"""
        print('\n'.join(self._collection.find(
            'status:error',
            item_format='{_ts} -> cmd={cmd} error_value={error_value}\n{traceback_string}\n',
            admin_fmt=True
        )))

    def history(self, *args):
        """Print/return successful colon commands used"""
        print('\n'.join(self._collection.find(
            'status:ok',
            item_format='{_ts} -> cmd={cmd} status={status}',
            admin_fmt=True
        )))
