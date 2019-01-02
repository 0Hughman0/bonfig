from abc import ABC
import functools


class BaseStore(ABC):

    @staticmethod
    def func_to_method(f, setter=False):
        if setter:
            @functools.wraps(f)
            def wrapped(self, *args, **kwargs):
                self.data = f(*args, **kwargs)
                return self.config.stores
        else:
            @functools.wraps(f)
            def wrapped(self, *args, **kwargs):
                return f(self.data, *args, **kwargs)
        return wrapped

    def chainify(self, f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            f(*args, **kwargs)
            return self.config.stores
        return wrapped

    def __init__(self, parent):
        self.config = parent

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, item):
        return item in self.data

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __eq__(self, other):
        return self.data == other
