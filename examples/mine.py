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
