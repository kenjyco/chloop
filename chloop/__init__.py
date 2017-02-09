import inspect
import socket
import sys
import time
import traceback
import click
import redis_helper as rh
from io import StringIO
from functools import partial
from pprint import pprint


chloop_logs = rh.Collection(
    'chloop-log',
    'default',
    index_fields='cmd,status,error_type',
    json_fields='args,value'
)


class GetCharLoop(object):
    """Loop forever, receiving character input from user and performing actions

    - ^d or ^c to break the loop
    - ':' to enter a command (and any arguments)
        - the name of the command should be monkeypatched on the GetCharLoop
          instance, or be a defined method on a GetCharLoop sub-class
        - the function bound to `:command` should accept `*args` only
    - '-' to receive an input line from user (a note)
    """
    def __init__(self, *args, **kwargs):
        """

        kwargs:

        - chfunc_dict: a dictionary where keys are characters and values are
          2-item tuples
            - first item is a function accepting no arguments
                - use `functools.partial` if needed
            - second item is some 'help text'
        - prompt: string to display when asking for input (default is '\n> ')
        - name: value of the 'name' argument for `redis_helper.Collection`
        """
        self._chfunc_dict = kwargs.pop('chfunc_dict', {})
        self._prompt = kwargs.pop('prompt', '\n> ')
        self._name = kwargs.pop('name', 'default')
        self._DONT_LOG_CMDS = [
            'docstrings', 'shortcuts', 'errors', 'history',
        ]
        self.collection = rh.Collection(
            'chloop-log',
            self._name,
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

    def __call__(self):
        while True:
            click.secho(self._prompt, nl=False, fg='cyan', bold=True)
            try:
                ch = click.getchar()
            except (EOFError, KeyboardInterrupt):
                break
            else:
                if ch in ['\x03','\x04']:
                    break

            if ch in self._chfunc_dict:
                print(ch)
                self._chfunc_dict[ch][0]()
            elif ch == '-':
                try:
                    user_input = click.prompt(text='', prompt_suffix='- ')
                    chloop_logs.add(cmd='-', user_input=user_input, status='ok')
                except click.exceptions.Abort:
                    print()
                    continue
            elif ch == ':':
                try:
                    user_input = click.prompt(text='', prompt_suffix=':')
                except click.exceptions.Abort:
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
                    if args:
                        cmd_func = partial(getattr(self, cmd), *args)
                    else:
                        cmd_func = getattr(self, cmd)
                except AttributeError:
                    chloop_logs.add(cmd=cmd, status='error', error_type='invalid command')
                    print('invalid command')
                    continue

                try:
                    value = cmd_func()
                    if cmd not in self._DONT_LOG_CMDS:
                        info = {
                            'status': 'ok',
                            'cmd': cmd,
                            'args': args,
                            'value': value
                        }
                    else:
                        info = {}
                except:
                    etype, evalue, tb = sys.exc_info()
                    epoch = time.time()
                    info = {
                        'status': 'error',
                        'cmd': cmd,
                        'traceback_string': traceback.format_exc(),
                        'error_type': repr(etype),
                        'error_value': repr(evalue),
                        'func': getattr(cmd_func, '__name__', ''),
                        'func_doc': getattr(cmd_func, '__doc__', ''),
                        'func_module': getattr(cmd_func, '__module__', ''),
                        'func_args': repr(args),
                        'fqdn': socket.getfqdn(),
                        'time_epoch': epoch,
                        'time_string': time.strftime(
                            '%Y_%m%d-%a-%H%M%S', time.localtime(epoch)
                        )
                    }
                    print('=' * 70)
                    print(info['traceback_string'])
                    print('cmd: {}\nargs: {}'.format(repr(cmd), repr(args)))

                if info:
                    chloop_logs.add(**info)
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
        fp.write('=' * 70 + '\n')
        class_doc = self._class_doc()
        fp.write(class_doc + '\n')

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
            for ch in sorted(self._chfunc_dict.keys()):
                line = '{} -- {}\n'.format(repr(ch), self._chfunc_dict[ch][1])
                fp.write(line)

        text = fp.getvalue()
        print(text)
        return text

    def errors(self, *args):
        """Print/return any colon commands that raised exceptions (w/ traceback)"""
        print('todo')

    def history(self, *args):
        """Print/return colon commands used"""
        print('todo')
