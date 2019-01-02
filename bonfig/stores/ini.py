import configparser

from .base import BaseStore


class INIStore(BaseStore):

    setters = ['read_file', 'read_string', 'read_dict', 'read_fp']

    def __init__(self, parent):
        super().__init__(parent)
        self.data = configparser.ConfigParser()

    def __getattr__(self, item):
        if item in self.setters:
            return self.chainify(getattr(self.data, item))
        raise AttributeError(item)
