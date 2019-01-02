import json

from .base import BaseStore


class JSONStore(BaseStore):

    def __init__(self, parent):
        super().__init__(parent)
        self.data = {}

    dumps = BaseStore.func_to_method(json.dumps)
    dump = BaseStore.func_to_method(json.dump)

    load = BaseStore.func_to_method(json.load, True)
    loads = BaseStore.func_to_method(json.loads, True)
