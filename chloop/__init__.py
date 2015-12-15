import inspect
import socket
import sys
import time
import traceback
from cStringIO import StringIO
from functools import partial
from pprint import pprint

import click
from redis_helper import (
    REDIS, next_object_id, index_hash_field, add_dict, getall_dicts
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
        - sep: delimiter character used to separate parts of a Redis key
        - prefix: string that all Redis keys should start with
        - prompt: string to display when asking for input
        - redis_client: an object returned by `redis.StrictRedis()`
        """
        self._chfunc_dict = kwargs.pop('chfunc_dict', {})
        self._keysep = kwargs.pop('sep', ':')
        self._keyprefix = kwargs.pop('prefix', '')
        self._prompt = kwargs.pop('prompt', '\n> ')
        self._redis = kwargs.pop('redis_client', REDIS)

        self._DONT_LOG_CMDS = [
            'errors', 'help', 'history', 'indices', 'session_keys',
            'session_notes'
        ]

        self._method_names = [
            m[0]
            for m in inspect.getmembers(self) if not m[0].startswith('_')
        ]
        self._method_docs = {
            method: getattr(self, method).__doc__ or ''
            for method in self._method_names
        }

        # Setup some things that Redis will use
        if self._keyprefix:
            self._base_keyname = next_object_id(
                '{}{}{}'.format(
                    self._keyprefix,
                    self._keysep,
                    self.__class__.__name__
                ),
                sep=self._keysep,
                redis_client=self._redis
            )
            self._indexpattern = '{}{}idx{}*'.format(
                self._keyprefix,
                self._keysep,
                self._keysep
            )
        else:
            self._base_keyname = next_object_id(
                '{}'.format(self.__class__.__name__),
                sep=self._keysep,
                redis_client=self._redis
            )
            self._indexpattern = 'idx{}*'.format(self._keysep)

        self._session_notes_key = '{}{}notes0'.format(
            self._base_keyname,
            self._keysep
        )

    def _redis_fullkey(self, keypart):
        """Given a specific part of a new Redis key, create/return the fullkey"""
        return next_object_id(
            '{}{}{}'.format(self._base_keyname, self._keysep, keypart),
            redis_client=self._redis
        )

    def _redis_add(self, keypart, somedict, indexfields=[]):
        """Add a python dictionary to Redis, at a specified keypart

        Generate full `hash_id` for the new object, then pass to the
        `redis_helper.add_dict` function.
        """
        hash_id = self._redis_fullkey(keypart)
        return add_dict(
            hash_id,
            somedict,
            indexfields,
            prefix=self._keyprefix,
            sep=self._keysep,
            use_time=True,
            redis_client=self._redis)

    def session_keys(self, display=True):
        """Display/return a list of keys (and their types) created for this session
        
        This is not every key in Redis that starts with `self._base_keyname`.
        The key names that end in a number are considered to be actual data that
        a user might care about (i.e. excluding '*next_id' keys).
        """
        sessionkeys = [
            {'type': self._redis.type(key), 'key': key}
            for key in self._redis.scan_iter(self._base_keyname + '*[0-9]')
        ]
        if display:
            print 'Redis keys for {}'.format(repr(self._base_keyname))
            pprint(sessionkeys)
        return sessionkeys

    def indices(self, display=True):
        """Display/return a list of Redis indices (and their types)
        
        These are indices created by the `redis_helper.index_hash_field`
        function for Python dicts added to Redis.
        """
        indices = [
            {'type': self._redis.type(key), 'key': key}
            for key in self._redis.scan_iter(self._indexpattern)
        ]
        if display:
            print 'Redis indices'
            pprint(indices)
        return indices

    def session_notes(self, key=None, time_format='%Y_%m%d-%a-%H%M%S',
                              display=True):
        """Return a string containing any notes made for GetCharLoop session 'key'

        - key: a Redis key to a sorted set containing notes (added by the '-'
          command); defaults to current `self._session_notes_key`
        - time_format: a strftime string for timestamp
            - see: http://strftime.org/
        - display: if True, display the string in addition to returning it
        """
        if not key:
            key = self._session_notes_key

        fp = StringIO()
        for note, epoch_time in self._redis.zrange(key, 0, -1, withscores=True):
            time_string = time.strftime(time_format, time.localtime(epoch_time))
            fp.write('- {}: {}\n'.format(time_string, note))

        text = fp.getvalue()
        if display:
            print 'Notes for {}'.format(repr(key))
            if text:
                print text
        return text
    
    def history(self):
        """Display command history for current session"""
        print 'Command history for {}'.format(repr(self._base_keyname))
        k = '{}{}cmd_results*[0-9]'.format(self._base_keyname, self._keysep)
        for key in self._redis.scan_iter(k):
            print '\n' + '~' * 70
            print key
            pprint(self._redis.hgetall(key))

    def errors(self):
        """Display command errors for current session"""
        print 'Command errors for {}'.format(repr(self._base_keyname))
        k = '{}{}error*[0-9]'.format(self._base_keyname, self._keysep)
        for key in self._redis.scan_iter(k):
            print '~' * 70
            print key
            data = self._redis.hgetall(key)
            traceback = data.pop('traceback_string')
            pprint(data)
            print '\n{}'.format(traceback)

    def __call__(self):
        while True:
            click.secho(self._prompt, nl=False, fg='cyan', bold=True)
            try:
                ch = click.getchar()
            except (EOFError, KeyboardInterrupt):
                break

            if ch in self._chfunc_dict:
                print ch
                self._chfunc_dict[ch][0]()
            elif ch == '-':
                epoch = time.time()
                try:
                    user_input = click.prompt(text='', prompt_suffix='- ')
                except click.exceptions.Abort:
                    print
                    continue
                self._redis.zadd(self._session_notes_key, epoch, user_input)
            elif ch == ':':
                try:
                    user_input = click.prompt(text='', prompt_suffix=':')
                except click.exceptions.Abort:
                    print
                    continue
                cmd = user_input.split()[0]
                args = user_input.split()[1:]

                if cmd == 'ipdb':
                    import ipdb; ipdb.set_trace()
                    continue

                try:
                    if args:
                        cmd_func = partial(getattr(self, cmd), *args)
                    else:
                        cmd_func = getattr(self, cmd)
                except AttributeError:
                    print 'invalid command'
                    continue

                try:
                    value = cmd_func()
                    if cmd not in self._DONT_LOG_CMDS:
                        info = {
                            'cmd': cmd,
                            'args': args,
                            'value': value
                        }
                        self._redis_add('cmd_results', info, indexfields=['cmd'])
                except:
                    etype, evalue, tb = sys.exc_info()
                    epoch = time.time()
                    info = {
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
                    print '=' * 70
                    print info['traceback_string']
                    print 'cmd: {}\nargs: {}'.format(repr(cmd), repr(args))
                    self._redis_add('error', info, indexfields=['func', 'error_type'])
            else:
                try:
                    print repr(ch), ord(ch)
                except TypeError:
                    # ord() expected a character, but string of length 2 found
                    #   - happens if you press 'Esc' before another key
                    print repr(ch)

    def ipdb(self):
        """Start ipdb (debugger). To continue back to the input loop, use 'c'

        ipdb> pp globals()
        ipdb> [x for x in dir(self) if not x.startswith('__')]
        ipdb> self._base_keyname
        ipdb> c
        """
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

        for method, docstring in sorted(self._method_docs.iteritems()):
            if docstring:
                fp.write('.:: {} ::.\n{}\n\n'.format(method, docstring.strip()))
            else:
                fp.write('.:: {} (no docs) ::.\n\n'.format(method))

        if self._chfunc_dict:
            for ch in sorted(self._chfunc_dict.iterkeys()):
                line = '{} -- {}\n'.format(repr(ch), self._chfunc_dict[ch][1])
                fp.write(line)

        text = fp.getvalue()
        print text
        return text
